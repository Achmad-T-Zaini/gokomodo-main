# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import format_date
from odoo.exceptions import UserError
import copy
import binascii
import struct
import time
import itertools
from collections import defaultdict

MAX_NAME_LENGTH = 50


class inventory_scm_delivery_report(models.AbstractModel):
    _inherit = 'account.report'
    _name = 'inventory.scm.delivery.report'
    _description = 'Inventory Delivery Order Report'

    filter_date = {'mode': 'range', 'filter': 'this_year'}
#    filter_all_entries = False
    filter_hierarchy = True
    filter_unfold_all = True

    def _get_report_name(self):
        return _('Inventory Table Report')

    def _get_templates(self):
        templates = super(inventory_scm_delivery_report, self)._get_templates()
        templates['main_template'] = 'gui_finance.main_template_inventory_transit_sales_report'
        return templates

    def get_header(self, options):
        start_date = format_date(self.env, options['date']['date_from'])
        end_date = format_date(self.env, options['date']['date_to'])
        return [
            [
                {'name': _('Sales Order No.'), 'class': 'text-center'},
                {'name': _('PO Customer'), 'class': 'text-center'},
                {'name': _('Customer'), 'class': 'text-center'},
                {'name': _('Province'), 'class': 'text-center'},
                {'name': _('Sales Person'), 'class': 'text-center'},
                {'name': _('Order Type'), 'class': 'text-center'},
                {'name': _('Route'), 'class': 'text-center'},
                {'name': _('Order Date'), 'class': 'text-center'},
                {'name': _('Approved Date'), 'class': 'text-center'},
                {'name': _('SJ No'), 'class': 'text-center'},
                {'name': _('Item Description'), 'class': 'text-center'},
                {'name': _('Order Qty'), 'class': 'text-center'},
                {'name': _('Done Qty'), 'class': 'text-center'},
                {'name': _('Status'), 'class': 'text-center'},
                {'name': _('Remarks'), 'class': 'text-center'},
                {'name': _('Delivery Date'), 'class': 'text-center'},
                {'name': _('Good Delivery Date'), 'class': 'text-center'},
                {'name': _('POD Receive Date'), 'class': 'text-center'},
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
            do_no = do_receive_date = status = approved_date = do_date = pod_date = origin = False
            approvals = self.env['approval.request'].search([('sale_id','=',so.id)],order='date_confirmed desc',limit=1)
            if approvals:
                approved_date = approvals.date_confirmed
            for picking in so.picking_ids:
                if picking.state!='cancel':
                    is_line2 = False
                    do_no = picking.name
                    do_date = picking.date_done
                    do_receive_date = picking.date_good_delivery
                    pod_date = picking.date_pod_done
                    if picking.status=='in_transit_delivery':
                        status = 'In Transit Delivery'
                    elif picking.status=='good_delivered':
                        status = 'Good Delivered'
                    elif picking.status=='draft':
                        status = 'Draft'
                    elif picking.status=='done':
                        status = 'Done'

                    if picking.origin[:6]=='Return':
                        origin = picking.origin

                    qty_done = ''
                    for picking_line in picking.move_ids_without_package:
                        qty_done = str(picking_line.product_uom_qty ) + '/' + str(picking_line.quantity_done)

                        line = {
                                'id': so.id,
                                'level': 1,
                                'name': so.name if len(so.name) < MAX_NAME_LENGTH else so.name[:MAX_NAME_LENGTH - 2] + '...',
                                'po': False,
                                'columns': [
                                    {'name': so.client_order_ref or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.partner_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.partner_id.state_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.user_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.order_type_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.route_id.warehouse_ids.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': so.date_order or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': approved_date or '', 'no_format_name': '', 'class': 'text-left'}, #approved date
                                    {'name': do_no or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': picking_line.sale_line_id.product_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': picking_line.sale_line_id.product_uom_qty, 'no_format_name': '', 'class': 'number'},
                                    {'name': qty_done, 'no_format_name': '', 'class': 'number'},
                                    {'name': status or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': origin or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': do_date or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': do_receive_date or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    {'name': pod_date or '', 'no_format_name': '', 'class': 'text-left'}, 
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

        date_to = options['date']['date_to']
        date_from = options['date']['date_from']

        results = self.env['sale.order'].search([('state','not in',['draft','sent','cancel']),('date_order','>=',date_from),('date_order','<=',date_to),('route_id.is_dropship','=',False)], order="name")
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
