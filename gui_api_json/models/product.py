# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import hashlib
import json

from odoo import api, models
from odoo.http import request
from odoo.tools import ustr

from odoo.addons.web.controllers.main import module_boot, HomeStaticTemplateHelpers

import odoo

class ProductProduct(models.Model):
    _inherit = 'product.product'


    def get_product_list(self):
        product_ids = []
        for rec in self:
            product_ids.append({ 'id': rec.id,
                                'name': rec.name,
                                })
        vals = { 'product_list': product_ids,}
        return vals


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def data_list(self):
        user = request.env.user

        user_context = request.session.get_context() if request.session.uid else {}
        IrConfigSudo = self.env['ir.config_parameter'].sudo()
        max_file_upload_size = int(IrConfigSudo.get_param(
            'web.max_file_upload_size',
            default=128 * 1024 * 1024,  # 128MiB
        ))

        api_data = {
            "uid": request.session.uid,
            "user_context": request.session.get_context() if request.session.uid else {},
            "db": request.session.db,
            "name": user.name,
            "username": user.login,
            "partner_display_name": user.partner_id.display_name,
            "company_id": user.company_id.id if request.session.uid else None,  # YTI TODO: Remove this from the user context
            "partner_id": user.partner_id.id if request.session.uid and user.partner_id else None,
            "web.base.url": IrConfigSudo.get_param('web.base.url', default=''),
            "active_ids_limit": int(IrConfigSudo.get_param('web.active_ids_limit', default='20000')),
            "max_file_upload_size": max_file_upload_size,
        }
        return api_data
