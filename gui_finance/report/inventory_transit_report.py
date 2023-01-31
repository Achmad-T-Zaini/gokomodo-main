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

MAX_NAME_LENGTH = 50


class inventory_transit_report(models.AbstractModel):
    _inherit = 'account.report'
    _name = 'inventory.transit.report'
    _description = 'Inventory Transit Sales Report'

#    filter_date = {'mode': 'range', 'filter': 'this_year'}
#    filter_all_entries = False
#    filter_hierarchy = True
#    filter_unfold_all = True

    def _get_report_name(self):
        return _('Inventory Table Report')

    def _get_templates(self):
        templates = super(inventory_transit_report, self)._get_templates()
        templates['main_template'] = 'gui_finance.main_template_inventory_transit_report'
        return templates

    def get_header(self, options):
#        start_date = format_date(self.env, options['date']['date_from'])
#        end_date = format_date(self.env, options['date']['date_to'])
        return [
            [
                {'name': _('Sales Order No.'), 'class': 'text-center'},
                {'name': _('PO Customer'), 'class': 'text-center'},
                {'name': _('Incoterm'), 'class': 'text-center'},
                {'name': _('Item Description'), 'class': 'text-center'},
                {'name': _('Quantity'), 'class': 'text-center'},
                {'name': _('Unit Price'), 'class': 'text-center'},
                {'name': _('Total'), 'class': 'text-center'},
                {'name': _('Expected DO Date'), 'class': 'text-center'},
                {'name': _('SJ No'), 'class': 'text-center'},
                {'name': _('Deliver qty'), 'class': 'text-center'},
                {'name': _('BAST No.'), 'class': 'text-center'},
                {'name': _('Status'), 'class': 'text-center'},
                {'name': _('Warehouse Location'), 'class': 'text-center'},
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
            do_no = bast_no = status = ""
            for picking in so.order_id.picking_ids:
                if picking.state!='cancel':
                    for rec in picking.move_ids_without_package:
                        sol_total_sales = rec.sale_line_id.product_uom_qty * rec.sale_line_id.price_unit
                        total_sales += sol_total_sales
                        qty_done = str(rec.product_uom_qty ) + '/' + str(rec.quantity_done)
                        do_no = picking.name
                        if picking.status=='draft':
                            status = 'Draft'
                        elif picking.status=='in_transit_delivery':
                            status = 'In Transit Delivery'
                        elif picking.status=='good_delivered':
                            status = 'Good Delivered'
                        elif picking.status=='done':
                            status = 'POD Received / Done'
                        line = {
                            'id': so.id,
                            'level': 1,
                            'name': so.name if len(so.name) < MAX_NAME_LENGTH else so.name[:MAX_NAME_LENGTH - 2] + '...',
                            'columns': [
                                {'name': so.client_order_ref or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': so.franco or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': rec.sale_line_id.product_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': rec.sale_line_id.product_uom_qty, 'no_format_name': ''},
                                {'name': self.format_value(rec.sale_line_id.price_unit), 'no_format_name': rec.sale_line_id.price_unit, 'class': 'number'},  
                                {'name': self.format_value(sol_total_sales ), 'no_format_name': sol_total_sales, 'class': 'number'},  
                                {'name': so.date_order or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': do_no or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': qty_done or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': bast_no or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': status or '', 'no_format_name': '', 'class': 'text-left'}, 
                                {'name': rec.sale_line_id.warehouse_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                            ],
                            'unfoldable': False,
                            'unfolded': False,
                            'caret_options': 'sale.order',
                        }
                        if len(so.name) >= MAX_NAME_LENGTH:
                            line.update({'title_hover': so.name})
                        lines.append(line)
        return lines

    def _get_sales_order(self, options):
        "Get the data from the database"

        results = self.env['sale.order'].search([('state','not in',['cancel'])], order="name")

        return results

    def open_data(self, options, params=None):
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
