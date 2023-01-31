# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import format_date
import copy
import binascii
import struct
import time
import itertools
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError

MAX_NAME_LENGTH = 50


class inventory_transit_dropship_report(models.AbstractModel):
    _inherit = 'account.report'
    _name = 'inventory.transit.dropship.report'
    _description = 'Inventory Transit Dropship Report'

#    filter_date = {'mode': 'range', 'filter': 'this_year'}
#    filter_all_entries = False
#    filter_hierarchy = True
#    filter_unfold_all = True

    def _get_report_name(self):
        return _('Inventory Table Report')

    def _get_templates(self):
        templates = super(inventory_transit_dropship_report, self)._get_templates()
        templates['main_template'] = 'gui_finance.main_template_inventory_transit_dropship_report'
        return templates

    def get_header(self, options):
#        start_date = format_date(self.env, options['date']['date_from'])
#        end_date = format_date(self.env, options['date']['date_to'])
        return [
            [
                {'name': _('Sales Order No.'), 'class': 'text-center'},
                {'name': _('Purchase Order No.'), 'class': 'text-center'},
                {'name': _('Incoterm'), 'class': 'text-center'},
                {'name': _('Item Description'), 'class': 'text-center'},
                {'name': _('Quantity'), 'class': 'text-center'},
                {'name': _('Unit Price'), 'class': 'text-center'},
                {'name': _('Total'), 'class': 'text-center'},
#                {'name': _('Expected Receive Date'), 'class': 'text-center'},
                {'name': _('Vendor Delivery Date'), 'class': 'text-center'},
                {'name': _('SJ No'), 'class': 'text-center'},
                {'name': _('Deliver qty'), 'class': 'text-center'},
                {'name': _('Customer Receive Date'), 'class': 'text-center'},
                {'name': _('Expected Customer Receive Date'), 'class': 'text-center'},
#                {'name': _('BAST No.'), 'class': 'text-center'},
                {'name': _('Status'), 'class': 'text-center'},
            ],
        ]

    @api.model
    def _init_filter_hierarchy(self, options, previous_options=None):
        # overwrite because we don't depend on account.group
        if self.filter_hierarchy is not None:
            if previous_options and 'hierarchy' in previous_options:
                options['hierarchy'] = previous_options['hierarchy']
            else:
                options['hierarchy'] = self.filter_hierarchy

    def _get_lines(self, options, line_id=None):
        options['self'] = self
        lines = []
        total_sales = 0
        sale_order = self._get_sales_order(options)
        for so in sale_order:
            do_no = bast_no = status = date_planned = purchase_order = sj_date = date_good_delivery = False
            for picking in so.picking_ids:
                if picking.state!='cancel':
                    for rec in picking.move_ids_without_package:
                        product_name = product_qty = product_price_unit = False
                        sol_total_sales = rec.sale_line_id.product_uom_qty * rec.sale_line_id.price_unit
                        total_sales += sol_total_sales
                        qty_done = str(rec.product_uom_qty ) + '/' + str(rec.quantity_done)
                        do_no = picking.name
                        do_date = picking.date_done
                        date_good_delivery = picking.date_good_delivery
                        if picking.status=='in_transit_delivery':
                            status = 'In Transit Delivery'
                        elif picking.status=='good_delivered':
                            status = 'Good Delivered'
                        elif picking.status=='draft':
                            status = 'Draft'
                        else:
                            status = False
                        sj_date = so.expected_date

                        if so.purchase_request_id:
                            for prl in so.purchase_request_id.line_ids:
                                if prl.product_id==rec.sale_line_id.product_id:
                                    for line in prl.purchase_lines:
                                        date_planned = line.order_id.date_planned
                                        purchase_order = line.order_id

                                    product_name = rec.sale_line_id.product_id.name
                                    product_qty = rec.sale_line_id.product_uom_qty
                                    product_price_unit = rec.sale_line_id.price_unit

                                elif not rec.sale_line_id:
                                    product_name = prl.product_id.name
                                    product_qty = prl.product_qty
                                    product_price_unit = prl.estimated_cost

                        line = {
                                'id': so.id,
                                'level': 1,
                                'name': so.name if len(so.name) < MAX_NAME_LENGTH else so.name[:MAX_NAME_LENGTH - 2] + '...',
                                'po': purchase_order.id if purchase_order else False,
                                'columns': [
                                    {'name': purchase_order.name if purchase_order else '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.franco or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': product_name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': product_qty, 'no_format_name': ''},
                                    {'name': self.format_value(product_price_unit), 'no_format_name': product_price_unit, 'class': 'number'},  
                                    {'name': self.format_value(sol_total_sales ), 'no_format_name': sol_total_sales, 'class': 'number'},  
#                                    {'name': date_planned or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': do_date or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': do_no or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': qty_done or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': date_good_delivery or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': sj_date or '', 'no_format_name': '', 'class': 'text-left'}, 
#                                    {'name': bast_no or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': status or '', 'no_format_name': '', 'class': 'text-left'}, 
                                ],
                                'unfoldable': False,
                                'unfolded': False,
                                'caret_options': 'sale.order',
                            }
                        if len(so.name) >= MAX_NAME_LENGTH:
                            line.update({'title_hover': so.name})
                        if status!=False:
                            lines.append(line)
        return lines

    def _get_sales_order(self, options):
        "Get the data from the database"

        results = self.env['sale.order'].search([('state','not in',['draft','sent','cancel']),('route_id.is_dropship','=',True)], order="name")

        return results

    def open_data_so(self, options, params=None):
        active_id = params.get('id')
        line = self.env['sale.order'].browse(active_id)
        return {
            'name': line.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'view_id': False,
            'views': [(self.env.ref('sale.view_order_form').id, 'form')],
            'res_id': line.id,
        }


    def open_data_so_po(self, options, params=None):
        active_id = params.get('id')
#        raise UserError(_('CP %s-%s')%(params,active_id))
        line = self.env['purchase.order'].browse(active_id)
        if line:
            return {
                'name': line.name,
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'view_id': False,
                'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
                'res_id': line.id,
            }
        return True

