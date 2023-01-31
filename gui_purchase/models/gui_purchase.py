from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_order_type(self):
        return self.env['sdt.order.type'].search([('sales_order_type','=','Jasa')],limit=1).id

### untuk membatasi create record pada tree - form PO berdasarkan order_type_id Jasa
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrder, self).fields_view_get(view_id=view_id, view_type=view_type,toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            root = etree.fromstring(res['arch'])
            root.set('create', 'false')
            res['arch'] = etree.tostring(root)

### untuk membatasi create record pada tree - form PO berdasarkan user yang memiliki role group_po_creator
        if view_type == 'tree' and not self.env.user.has_group("gui_resource_customs.group_po_creator"):
            root = etree.fromstring(res['arch'])
            root.set('create', 'false')
            res['arch'] = etree.tostring(root)
        return res

    terbilang = fields.Text(string='Terbilang', copy=False, store=False, compute="_compute_terbilang")
    notes = fields.Text('Terms and Conditions',
            default="""
1. PO harus ditanda tangani dan dikirim kembali ke kami via email dalam kurun waktu maksimal 2 (dua) hari kerja.<br/>
2. Item dan Brand item yang tertera pada PO tidak boleh diubah tanpa adanya persetujuan dari kami.<br/>
3. Perusahaan berhak untuk mengembalikan barang yang tidak sesuai dengan spesifikasi atau cacat pada saat diterima.<br/>
4. Mohon mencantumkan nomor PO pada invoice / tagihan dan surat jalan.<br/>
5. Mohon invoice dapat dikirim ke Grand ITC Permata Hijau - Jl. Arteri Permata Hijau No. 11, RT.11/RW.10, Grogol Utara,
Kec. Kby. Lama, Kota Jakarta Selatan, Daerah Khusus Ibukota Jakarta 12210. (PIC : Mega - 0888028193798).<br/>
""")
    order_type_id = fields.Many2one(string='Order Type', comodel_name='sdt.order.type', default=_default_order_type, readonly=True)
    order_line_nc = fields.One2many('purchase.order.line', 'order_id', string='Order Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)

    @api.model
    def create(self, vals):
        if vals.get('group_id',False):
            group_id = self.env['procurement.group'].search([('id','=',vals['group_id'])])
            if group_id.sale_id:
                vals['order_type_id'] = group_id.sale_id.order_type_id.id
                vals['user_id'] = group_id.sale_id.user_id.id
        return super(PurchaseOrder, self).create(vals)

    @api.depends('amount_total')
    def _compute_terbilang(self):
        self.ensure_one()
        if self.amount_total and self.amount_total>0:
            self.update({'terbilang': self.env['account.terbilang'].terbilang(self.amount_total) + self.currency_id.currency_unit_label})

    def button_draft(self):
        self.write({'state': 'draft', 'approval_request_id': False})
        return {}

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    order_type_id = fields.Many2one(string='Order Type', comodel_name='sdt.order.type', related="order_id.order_type_id")

    @api.onchange('order_type_id')
    def onchange_order_type_id(self):
        if not self.order_type_id and self.order_type_id.id==3:
            product_ids = [x.id for x in self.env['product.product'].search([('purchase_ok','=',True),('type','=','product')])]
        else:
            product_ids = [x.id for x in self.env['product.product'].search([('purchase_ok','=',True),('type','=','service')])]
        return {'domain': {'product_id': [('id','in',product_ids)]}}

    @api.model
    def create(self, vals):
        if vals.get('order_id',False):
            purchase_id = self.env['purchase.order'].search([('id','=',vals['order_id'])])
            if purchase_id:
                group_id = purchase_id.group_id
                vals['order_type_id'] = group_id.sale_id.order_type_id.id
                sol = group_id.sale_id.mapped("order_line").filtered(lambda l: l.product_id.id == vals['product_id'] and l.product_uom_qty==vals['product_qty'])
                if sol:
                    vals['sale_line_id'] = sol[0].id 
        return super(PurchaseOrderLine, self).create(vals)


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    def set_req_to_so(self):
        for req in self:
            for so in req.sale_id:
                wh = so.warehouse_id
                if so.purchase_request_id:
                    if so.route_id:
                        for route in so.route_id.rule_ids:
                            wh = route.picking_type_id.warehouse_id
                so.write({'purchase_request_id': req.id, 'warehouse_id': wh.id})
# Penambahan rule supaya SO Warehouse mengikuti SO Route saat dilakukan Req Approval PR

    def button_draft(self):
        self.mapped("line_ids").do_uncancel()
        return self.write({"state": "draft", "approval_request_id": False,})

    @api.model
    def create(self, vals):
        if vals.get('group_id',False):
            group_id = self.env['procurement.group'].search([('id','=',vals['group_id'])])
            if group_id.sale_id:
                vals['order_type_id'] = group_id.sale_id.order_type_id.id
                vals['requested_by'] = group_id.sale_id.user_id.id
                vals['sale_id'] = group_id.sale_id.id
        return super(PurchaseRequest, self).create(vals)

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    def get_data(self,sale_id,product_id):
        data = {}
        for sol in sale_id.order_line:
            if not sol.is_downpayment and sol.product_id.id==product_id:
                data = {
                        'product_id': sol.product_id.id,
                        'name': sol.name,
                        'product_qty': sol.product_uom_qty,
                        'product_uom_id': sol.product_uom.id,
                        'date_required': fields.date.today(),
                        'estimated_cost': sol.cost_market,
                        'total_estimated_cost': sol.product_uom_qty * sol.cost_market,
                        'currency_id': sol.currency_id.id,
                        'company_id': sol.company_id.id,
                        'sale_line_id': sol.id,
                    }
        return data

    @api.model
    def create(self, vals):
        if vals.get('request_id',False):
            request_id = self.env['purchase.request'].search([('id','=',vals['request_id'])])
            if request_id.sale_id:
                prl_vals = self.get_data(request_id.sale_id,vals['product_id'],)
                prl_vals['request_id'] = vals['request_id']
                vals['estimated_cost'] = prl_vals['estimated_cost']
                vals['total_estimated_cost'] = prl_vals['total_estimated_cost']
                vals['sale_line_id'] = prl_vals['sale_line_id']
        return super(PurchaseRequestLine, self).create(vals)
