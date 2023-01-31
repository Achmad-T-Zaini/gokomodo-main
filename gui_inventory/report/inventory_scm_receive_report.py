# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError
import copy
import binascii
import struct
import time
import itertools
from collections import defaultdict

MAX_NAME_LENGTH = 50


class inventory_scm_receive_report(models.AbstractModel):
    _inherit = 'account.report'
    _name = 'inventory.scm.receive.report'
    _description = 'Inventory Receive Order Report'

    filter_date = {'mode': 'range', 'filter': 'this_year'}
#    filter_all_entries = False
    filter_hierarchy = True
    filter_unfold_all = True

    def _get_report_name(self):
        return _('Inventory Table Report')

    def _get_templates(self):
        templates = super(inventory_scm_receive_report, self)._get_templates()
        templates['main_template'] = 'gui_finance.main_template_inventory_transit_purchase_report'
        return templates

    def get_header(self, options):
        start_date = format_date(self.env, options['date']['date_from'])
        end_date = format_date(self.env, options['date']['date_to'])
        return [
            [
                {'name': _('Purchase Order No.'), 'class': 'text-center'},
                {'name': _('Sales Order No.'), 'class': 'text-center'},
                {'name': _('PO Customer'), 'class': 'text-center'},
                {'name': _('Vendor'), 'class': 'text-center'},
                {'name': _('Vendor Reff'), 'class': 'text-center'},
                {'name': _('Order Type'), 'class': 'text-center'},
                {'name': _('Route'), 'class': 'text-center'},
                {'name': _('PO Date'), 'class': 'text-center'},
                {'name': _('Approved Date'), 'class': 'text-center'},
                {'name': _('Released Date'), 'class': 'text-center'},
                {'name': _('Item Description'), 'class': 'text-center'},
                {'name': _('Quantity'), 'class': 'text-center'},
                {'name': _('SJ No'), 'class': 'text-center'},
                {'name': _('Done Qty'), 'class': 'text-center'},
                {'name': _('Status'), 'class': 'text-center'},
                {'name': _('Receive Date'), 'class': 'text-center'},
                {'name': _('Remark'), 'class': 'text-center'},
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
        purchase_order = self._get_purchase_order(options)
        for po in purchase_order:
            do_no = status = qty_done = do_date = pod_date = so_name = po_customer = approved_date = origin = False
            if po.origin and po.origin[:1]=='S':
                so_name = po.origin
                sale_order = self.env['sale.order'].search([('name','=',po.origin)],limit=1)
                if sale_order:
                    po_customer = sale_order.client_order_ref
            approvals = self.env['approval.request'].search([('purchase_order_id','=',po.id)],order='date_confirmed desc',limit=1)
            if approvals:
                approved_date = approvals.date_confirmed

            for picking in po.picking_ids:
                if picking.state!='cancel':
                    for rec in picking.move_ids_without_package:
                        pol_total_sales = rec.purchase_line_id.product_uom_qty * rec.purchase_line_id.price_unit
                        total_sales += pol_total_sales
                        qty_done = str(rec.product_uom_qty ) + '/' + str(rec.quantity_done)
                        do_no = picking.name
                        do_date = picking.scheduled_date
                        pod_date = picking.date_done
                        if picking.state=='assigned':
                            status = 'Ready'
                        else:
                            status = picking.state

                        if picking.origin!=po.name:
                            origin = picking.origin


                        if not po.picking_type_id.warehouse_id.is_dropship and not po.dest_address_id:
                            line = {
                                    'id': po.id,
                                    'level': 1,
                                    'name': po.name if len(po.name) < MAX_NAME_LENGTH else po.name[:MAX_NAME_LENGTH - 2] + '...',
                                    'po': False,
                                    'columns': [
                                        {'name': so_name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': po_customer or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': po.partner_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': po.partner_ref or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': po.order_type_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': po.picking_type_id.display_name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': po.date_order or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': approved_date or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': do_date or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': rec.purchase_line_id.product_id.name or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': rec.purchase_line_id.product_uom_qty, 'no_format_name': '', 'class': 'number'},
                                        {'name': do_no or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': qty_done, 'no_format_name': '', 'class': 'number'},
                                        {'name': status or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': pod_date or '', 'no_format_name': '', 'class': 'text-left'}, 
                                        {'name': origin or '', 'no_format_name': '', 'class': 'text-left'}, 
                                    ],
                                    'unfoldable': False,
                                    'unfolded': False,
                                    'caret_options': 'purchase.order',
                                }
                            if len(po.name) >= MAX_NAME_LENGTH:
                                line.update({'title_hover': po.name})
                            if status!=False:
                                lines.append(line)
        return lines

    def _get_purchase_order(self, options):
        "Get the data from the database"

        date_to = options['date']['date_to']
        date_from = options['date']['date_from']

        results = self.env['purchase.order'].search([('state','not in',['draft','sent','cancel']),('date_order','>=',date_from),('date_order','<=',date_to)], order="name")

        return results

    def open_data_po(self, options, params=None):
        active_id = params.get('id')
        line = self.env['purchase.order'].browse(active_id)
        return {
            'name': line.name,
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'view_id': False,
            'views': [(self.env.ref('purchase.purchase_order_form').id, 'form')],
            'res_id': line.id,
        }
