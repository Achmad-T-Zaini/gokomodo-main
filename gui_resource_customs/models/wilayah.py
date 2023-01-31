# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode



class CountryState(models.Model):
    _inherit = 'res.country.state'

    city_ids = fields.One2many('res.state.city', 'state_id', string='City', store=True, copy=False)

class StateCity(models.Model):
    _name = "res.state.city"
    _description = "Kabupaten Kota"
    _order = 'id desc'


    name = fields.Char(string='Kabupaten/Kota', required=True, copy=False, index=True, default=lambda self: _('New'))
    code = fields.Char(string='Kode', required=True, copy=False, index=True, default=lambda self: _('Kode'))
    state_id = fields.Many2one('res.country.state', string='Provinsi')
    country_id = fields.Many2one('res.country', string='Country', related='state_id.country_id')
    district_ids = fields.One2many('res.city.district','city_id', string='Kecamatan')


class CityDistrict(models.Model):
    _name = "res.city.district"
    _description = "Kecamatan"
    _order = 'id desc'


    name = fields.Char(string='Kecamatan', required=True, copy=False, index=True, default=lambda self: _('New'))
    code = fields.Char(string='Kode', required=True, copy=False, index=True, default=lambda self: _('Kode'))
    city_id = fields.Many2one('res.state.city', string='Kabupaten/Kota')
    state_id = fields.Many2one('res.country.state', string='Provinsi', related='city_id.state_id')
    country_id = fields.Many2one('res.country', string='Country', related='city_id.state_id.country_id')
    village_ids = fields.One2many('res.district.village','district_id', string='Kelurahan')

class DistrictVillage(models.Model):
    _name = "res.district.village"
    _description = "Kelurahan"
    _order = 'id desc'


    name = fields.Char(string='Kelurahan', required=True, copy=False, index=True, default=lambda self: _('New'))
    code = fields.Char(string='Kode', required=True, copy=False, index=True, default=lambda self: _('Kode'))
    district_id = fields.Many2one('res.city.district', string='Kecamatan')
    kodepos = fields.Char(string='Kodepos')    
    city_id = fields.Many2one('res.state.city', string='Kabupaten/Kota', related='district_id.city_id')
    state_id = fields.Many2one('res.country.state', string='Provinsi', related='district_id.city_id.state_id')
    country_id = fields.Many2one('res.country', string='Country', related='district_id.city_id.state_id.country_id')

