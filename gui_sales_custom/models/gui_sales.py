
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SalesTeam(models.Model):
    _inherit = 'crm.team'

    employee_ids = fields.One2many('hr.employee','sales_team_id',string='Employee Member', store=True, copy=False)
    department_id = fields.Many2one('hr.department', string='Department', required=True)

    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id:
            dept_ids = self.env['hr.department'].search([('id','child_of',self.department_id.id)])
            emp_ids = self.employee_ids.filtered(lambda line: line.department_id in dept_ids)
#            self.employee_ids = [(0,0, employee) for employee in emp_ids]

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    sales_team_id = fields.Many2one('crm.team',string='Sales Team', store=True, copy=False)

class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    sales_team_id = fields.Many2one(readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sales_person_employee = fields.Many2one('hr.employee',string='Sales Person', 
        domain="[('sales_team_id', '=', team_id)]",)
    order_type_id = fields.Many2one(string='Order Type', comodel_name='sdt.order.type')
    sales_order_type = fields.Selection(string='Sales Order Type',
        selection=[
            ('Corporate', 'Corporate'),
            ('Retail', 'Retail'),
            ('Jasa', 'Jasa'),
            ('Subscription', 'Subscription'),
            ],
        default="Corporate", related='order_type_id.sales_order_type')

    terbilang = fields.Text(string='Terbilang', copy=False, store=False, compute="_compute_terbilang")
    route_id = fields.Many2one(required=False, store=True, copy=False)

    @api.onchange('order_type_id')
    def _get_order_type(self):
        if self.order_type_id:
            self.payment_term_id = False
            if self.partner_id and self.partner_id.property_payment_term_id:
                self.payment_term_id = self.partner_id.property_payment_term_id.id
            partner_obj = self.env['res.partner'].search([('category_id', '=', 'Customer')])
            domain = {'partner_id': [('id', 'in', (partner_obj.ids)),]}
        else:
            domain = {'partner_id': [('id', '=', False)]}
        return {'domain': domain}

    @api.onchange('team_id')
    def onchange_team_id(self):
        team_domain = False
        if self.team_id:
            sales_employee = self.env['hr.employee'].search([('sales_team_id','=',self.team_id.id)])
            team_domain = {'domain': {'sales_person_employee': [('id', 'in', sales_employee.ids)]}}
            self.sales_person_employee = False
        return team_domain

    @api.depends('amount_total')
    def _compute_terbilang(self):
        self.ensure_one()
        self.terbilang=False
        if self.amount_total and self.amount_total>0:
            self._amount_by_group()
            self.update({'terbilang': self.env['account.terbilang'].terbilang(self.amount_total) + self.currency_id.currency_unit_label})

    @api.onchange('sales_person_employee')
    def onchange_sales_person_employee(self):
        if self.sales_person_employee and self.sales_person_employee.user_id:
            self.user_id = self.sales_person_employee.user_id.id
        elif self.sales_person_employee:
            raise UserError(_("Employee %s doesn't have user_id, please contact Adminstrator")%(self.sales_person_employee.name,))

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.route_id:
            self.warehouse_id = self.route_id.rule_ids.picking_type_id.warehouse_id
        elif self.state in ['draft','sent']:
            self.warehouse_id = self.user_id.with_company(self.company_id.id)._get_default_warehouse_id().id
            # Perubahan warehouse_id depends on perubahan route_id (jika ada route_id)
            # jika route_id=False/blank, maka warehouse_id akan mengikuti rule default user_id 

    @api.onchange('route_id')
    def sdt_onchange_route_id(self):
        if not self.route_id:
            return
        else:
            self.warehouse_id = self.route_id.rule_ids.picking_type_id.warehouse_id

    
    @api.model
    def create(self, vals):
        res = super(SaleOrder,self).create(vals)
        for sale in res:
            for sol in sale.order_line:
                if not sale.franco:
                    if sol.product_id.product_tmpl_id.toleransi:
                        raise UserError("Franco is required!")
                if sale.sales_order_type!='Subscription' and sale.sales_order_type!='Jasa':
                    if sol.cost_market <= 0 and not sol.is_downpayment:
                        raise UserError("Cost market is required or can't be minus")
        return res

    def write(self, values):
        res = super(SaleOrder,self).write(values)
        for sol in self.order_line:
            if not self.franco:
                if sol.product_id.product_tmpl_id.toleransi:
                    raise UserError("Franco is required!")
            if self.sales_order_type!='Subscription' and self.sales_order_type!='Jasa':
                if sol.cost_market <= 0 and not sol.is_downpayment and sol.price_total>0:
                    raise UserError("Cost market is required or can't be minus ")
        return res

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        return orders.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
            'signed_on': False,
            'state_approval_cm': False,
            'state_approval_fm': False,
        })


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cost_market = fields.Float(string='Cost Market', default=False, store=True)
    order_type_id = fields.Many2one(string='Order Type', comodel_name='sdt.order.type', related="order_id.order_type_id")
    sales_order_type = fields.Selection(string='Sales Order Type',
        selection=[
            ('Corporate', 'Corporate'),
            ('Retail', 'Retail'),
            ('Jasa', 'Jasa'),
            ('Subscription', 'Subscription'),
            ],
        default="Corporate", related='order_type_id.sales_order_type')

    @api.onchange('order_type_id')
    def onchange_order_type_id(self):
        if self.order_type_id and self.order_type_id.sales_order_type=='Jasa':
            product_ids = [x.id for x in self.env['product.product'].search([('sale_ok','=',True),('type','=','service'),('recurring_invoice','=',False)])]
        elif self.order_type_id and self.order_type_id.sales_order_type=='Subscription':
            product_ids = [x.id for x in self.env['product.product'].search([('sale_ok','=',True),('recurring_invoice','=',True)])]
        elif self.order_type_id:
            product_ids = [x.id for x in self.env['product.product'].search([('sale_ok','=',True),('type','=','product')])]
        else:
            product_ids = [x.id for x in self.env['product.product'].search([('sale_ok','=',True)])]
        return {'domain': {'product_id': [('id','in',product_ids)]}}

    @api.onchange('cost_market', 'price_unit')
    def _get_price_margin(self):
        for line in self:
            if line.cost_market != 0 and line.price_unit:
                margin = ((line.price_unit - line.cost_market) / line.cost_market)*100
                line.price_margin = margin
                if line.price_margin < line.product_id.price_margin_percentage:
                   line.less_margin = True 
                else:
                    line.less_margin = False
            elif line.cost_market == 0 and line.price_unit and line.order_type_id.sales_order_type=='Subscription':
                line.price_margin = 100
                line.less_margin = False

    @api.model
    def create(self, vals):
        if vals.get('order_id',False):
            so = self.env['sale.order'].search([('id','=',vals['order_id'])])
            if so:
                vals['order_type_id'] = so.order_type_id.id
        res = super(SaleOrderLine,self).create(vals)
        return res

    def write(self, values):
        res = super(SaleOrderLine,self).write(values)
        return res


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = {
            'ref': order.client_order_ref,
            'move_type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'sales_person_employee': order.sales_person_employee.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(order.partner_id.id)).id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_reference': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id if not so_line.display_type and order.analytic_account_id.id else False,
            })],
        }

        return invoice_vals
