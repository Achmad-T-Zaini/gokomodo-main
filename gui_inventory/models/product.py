# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import hashlib
import json


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_corporate = fields.Boolean('Corporate', store=True, default=False)
    is_retail = fields.Boolean('Retail', store=True, default=False)

class ProductCategory(models.Model):
    _inherit = "product.category"

    code = fields.Char(string="Internal Code", store=True, copy=False)


    @api.depends('name', 'parent_id.complete_name', 'code')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = '%s / %s' % (category.code, category.name)
#                category.complete_name = category.code + " " + category.name
