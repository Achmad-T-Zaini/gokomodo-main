# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.tools.misc import groupby

class SDTReportView(models.TransientModel):
    _inherit = "sdt.report.view"

    total_sales = fields.Float()
    sale_cost = fields.Float()
    sale_margin = fields.Float()
    sale_margin2cost = fields.Float()
    sale_margin2sale = fields.Float()
    customer = fields.Char()
    provinsi = fields.Char()
    sales = fields.Char()
    order_type = fields.Char()
    route = fields.Char()
    status = fields.Char()


class SDTReport(models.TransientModel):
    _inherit = "report.sdt.report"


    def _compute_results(self):
        self.ensure_one()
        date_from = self.date_from or "0001-01-01"
        date_to = self.date_to or fields.Date.context_today(self)
        company_id = self.env.company.id
        
        stock_card_results = []
        sale_line_ids = self.env['sale.order.line'].search([('order_id.date_order','>=',date_from),('order_id.date_order','<=',date_to),('company_id','<=',company_id),('state','in',['sale','done'])])
        for sale in sale_line_ids:
            delivered = self._get_delivered(date_from, date_to, sale, company_id)
            qty_delivered = self._get_qty_delivered(date_from, date_to, sale, company_id)
            invoice = self._get_invoice(date_from, date_to, sale, company_id)
            # qty_invoice = self._get_qty_invoice(date_from, date_to, sale, company_id)
            qty_invoice = sale.qty_invoiced
            credit_note = self._get_credit_note(date_from, date_to, sale, company_id)
            qty_credit_note = self._get_qty_credit_note(date_from, date_to, sale, company_id)
            request = self._get_request(date_from, date_to, sale, company_id)
            qty_request = self._get_qty_request(date_from, date_to, sale, company_id)
            purchase = self._get_purchase(date_from, date_to, sale, company_id)
            qty_purchase = self._get_qty_purchase(date_from, date_to, sale, company_id)
            received = self._get_received(date_from, date_to, sale, company_id)
            qty_received = self._get_qty_received(date_from, date_to, sale, company_id)
            bill = self._get_bill(date_from, date_to, sale, company_id)
            qty_bill = self._get_qty_bill(date_from, date_to, sale, company_id)
            refund = self._get_refund(date_from, date_to, sale, company_id)
            qty_refund = self._get_qty_refund(date_from, date_to, sale, company_id)
            pol_cost = self.env['purchase.order.line'].search([('sale_line_id','=',sale.id),('state','!=','cancel')],limit=1)
            if pol_cost:
                sale_cost = pol_cost.price_unit
                sale_margin = sale.price_unit - sale_cost 
                sale_margin2cost = sale_margin / sale_cost * 100
                sale_margin2sale = sale_margin / sale.price_unit * 100
            else:
                sale_cost = sale_margin = sale_margin2cost = sale_margin2sale = 0

            total_sales = pol_cost.price_unit * pol_cost.product_uom_qty

            if sale.order_id.state=='done':
                sale_status = 'Locked'
            elif sale.order_id.state=='cancel':
                sale_status = 'Cancelled'
            elif sale.order_id.state=='sent':
                sale_status = 'Quotation Sent'
            elif sale.order_id.state=='sale':
                sale_status = 'Sale Order'
            else:
                sale_status = 'Quotation'

            result = {
                'sale_id': sale.order_id.id,
                'customer': sale.order_id.partner_id.name,
                'provinsi': sale.order_id.partner_id.state_id.name or '',
                'sales': sale.order_id.user_id.name,
                'order_type': sale.order_id.order_type_id.name,
                'route': sale.order_id.route_id.name,
                'status': sale_status,
                'product_id': sale.product_id.id,
                'qty_order': sale.product_uom_qty,
                'product_uom_id': sale.product_uom,
                'total_sales': total_sales,
                'price_unit': sale.price_unit,
                'delivered': delivered,
                'qty_delivered': qty_delivered,
                'invoice': invoice,
                'qty_invoice': qty_invoice,
                'credit_note': credit_note,
                'qty_credit_note': qty_credit_note,
                'request': request,
                'qty_request': qty_request,
                'purchase': purchase,
                'qty_purchase': qty_purchase,
                'received': received,
                'qty_received': qty_received,
                'bill': bill,
                'qty_bill': qty_bill,
                'refund': refund,
                'qty_refund': qty_refund,
# Additional for ODP-12
                'sale_cost': sale_cost,
                'sale_margin': sale_margin,
                'sale_margin2cost': sale_margin2cost,
                'sale_margin2sale': sale_margin2sale,
            }
            stock_card_results.append(result)
        

        ReportLine = self.env["sdt.report.view"]
        self.results = [ReportLine.new(line).id for line in stock_card_results]

    def _get_delivered(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT p.name 
            FROM stock_picking p 
            INNER JOIN stock_move m on m.picking_id=p.id 
            WHERE p.sale_id = %s
                and p.state = 'done'
                and m.sale_line_id = %s
                and p.company_id = %s
        """,
            (sale.order_id.id,sale.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_invoice(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct a.name 
            FROM account_move a 
            INNER JOIN account_move_line aml on aml.move_id=a.id 
            WHERE a.invoice_origin = %s
                and a.move_type='out_invoice'
                and a.state = 'posted'
                and aml.exclude_from_invoice_tab = False
                and aml.product_id = %s
                and a.company_id = %s
        """,
            (sale.order_id.name,sale.product_id.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_credit_note(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct a.name 
            FROM account_move a 
            INNER JOIN account_move_line aml on aml.move_id=a.id 
            WHERE a.invoice_origin = %s
                and a.move_type='out_refund'
                and a.state = 'posted'
                and aml.exclude_from_invoice_tab = False
                and aml.product_id = %s
                and a.company_id = %s
        """,
            (sale.order_id.name,sale.product_id.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_request(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct pr.name 
            FROM purchase_request pr 
            INNER JOIN purchase_request_line prl on prl.request_id=pr.id
            WHERE prl.origin = %s
                and prl.request_state not in ('draft','cancel')
                and prl.sale_line_id = %s
                and prl.company_id = %s
        """,
            (sale.order_id.name,sale.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_purchase(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct po.name 
            FROM purchase_order po 
            INNER JOIN purchase_order_line pol on pol.order_id=po.id
            WHERE pol.sale_order_id = %s
                and pol.state not in ('draft','cancel')
                and pol.sale_line_id = %s
                and pol.company_id = %s
        """,
            (sale.order_id.id,sale.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_received(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct p.name 
            FROM stock_picking p 
            INNER JOIN stock_move m on m.picking_id=p.id 
            LEFT JOIN purchase_order po on po.name=p.origin
            LEFT JOIN purchase_order_line pol on pol.order_id=po.id and m.purchase_line_id=pol.id
            WHERE p.state = 'done'
                and po.origin = %s
                and pol.product_id = %s
                and p.company_id = %s
        """,
            (sale.order_id.name,sale.product_id.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_bill(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct a.name 
            FROM account_move a 
            INNER JOIN account_move_line aml on aml.move_id=a.id 
            WHERE a.invoice_origin = %s
                and a.move_type='in_invoice'
                and a.state = 'posted'
                and aml.exclude_from_invoice_tab = False
                and aml.product_id = %s
                and a.company_id = %s
        """,
            (sale.order_id.name,sale.product_id.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]

    def _get_refund(self, date_from, date_to, sale, company_id):
        self._cr.execute(
            """
            SELECT distinct a.name 
            FROM account_move a 
            INNER JOIN account_move_line aml on aml.move_id=a.id 
            WHERE a.invoice_origin = %s
                and a.move_type='in_refund'
                and a.state = 'posted'
                and aml.exclude_from_invoice_tab = False
                and aml.product_id = %s
                and a.company_id = %s
        """,
            (sale.order_id.name,sale.product_id.id,company_id,),
        )
        res = self._cr.dictfetchall()
        result = ""
        for r in res:
            result +=r['name'] + ','
        return result[:-1]
