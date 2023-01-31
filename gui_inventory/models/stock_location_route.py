# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import hashlib
import json


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, date_utils


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    is_dropship = fields.Boolean('Dropship Route', store=True, default=False)

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    is_dropship = fields.Boolean('Dropship Warehouse', store=True, default=False)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    cek_status = fields.Char(String='cek status', compute='_onchange_secondary_status')

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        if vals.get('status',False):
            if vals['status']=='in_transit_delivery':
                vals['status']='draft'

        if vals.get('force_date',False):
            vals['force_date']=False

        return res

#    def write(self,vals):
#        raise UserError(_('vals %s')%(vals))
#        res = super(StockPicking, self).create(vals)
#        return res




    @api.depends('status','state')
    def _onchange_secondary_status(self):
        for rec in self:
            if rec.state=='done' and rec.bool_pod_done:
                status='done'
            elif rec.state=='done' and rec.bool_good_delivery:
                status='good_delivered'
            elif rec.state=='done' and not rec.bool_good_delivery:
                status='in_transit_delivery'
            else:
                status='draft'
            rec.update({'cek_status': status, 'status': status,})


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"


    def write(self, vals):
        if vals.get('status',False):
            if vals['status']=='in_transit_delivery' and self.state!='done':
                vals['status']='draft'
        return super(StockMoveLine, self).write(vals)


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for pick_id in pickings_not_to_do:
            moves_to_log = {}
            for move in pick_id.move_lines:
                if float_compare(move.product_uom_qty,
                                 move.quantity_done,
                                 precision_rounding=move.product_uom.rounding) > 0:
                    moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
            pick_id._log_less_quantities_than_expected(moves_to_log)

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(skip_backorder=True)
            if pickings_not_to_do:
                pickings_to_validate = pickings_to_validate.with_context(picking_ids_not_to_backorder=pickings_not_to_do.ids)
            res = pickings_to_validate.button_validate()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
