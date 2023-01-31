# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    city_id = fields.Many2one('res.state.city',string='Kab / Kota', domain="[('state_id','=',state_id)]")

    @api.onchange('state_id')
    def onchange_state_id(self): 
        self.city_id = False
        if self.state_id:
            city_ids = [x.id for x in self.env['res.state.city'].search([('state_id','=',self.state_id.id)])]
        else:
            city_ids = [x.id for x in self.env['res.state.city'].search([('country_id','=',self.env.user.company_id.country_id.id)])]
        return {'domain': {'city_id': [('id','in',city_ids)]}}

    @api.onchange('city_id')
    def onchange_city_id(self): 
        if self.city_id:
            self.city = self.city_id.name
        else:
            self.city = False
