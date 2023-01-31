# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import babel.messages.pofile
import base64
import copy
import datetime
import functools
import glob
import hashlib
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict, defaultdict, Counter
from werkzeug.urls import url_encode, url_decode, iri_to_uri
from lxml import etree
import unicodedata


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.models import check_method_name
from odoo.service import db, security

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import groupby as groupbyelem

from odoo.osv.expression import OR
from odoo.addons.gui_api_json.common import extract_arguments, invalid_response, valid_response

_logger = logging.getLogger(__name__)
_routes = ["/gui_api/<model>", "/gui_api/<model>/<id>", "/api/<model>/<id>/<action>"]

class Session(http.Controller):

    @http.route('/gui_api/session/get_session_info', type='json', auth="none")
    def get_session_info_gui(self):
        request.session.check_security()
        request.uid = request.session.uid
        request.disable_db = False
        return request.env['ir.http'].session_info_gui()

    @http.route('/gui_api/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None):
        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info_gui()

    @http.route('/gui_api/session/change_password', type='json', auth="user")
    def change_password(self, fields):
        old_password, new_password,confirm_password = operator.itemgetter('old_pwd', 'new_password','confirm_pwd')(
            {f['name']: f['value'] for f in fields})
        if not (old_password.strip() and new_password.strip() and confirm_password.strip()):
            return {'error':_('You cannot leave any password empty.'),'title': _('Change Password')}
        if new_password != confirm_password:
            return {'error': _('The new password and its confirmation must be identical.'),'title': _('Change Password')}

        msg = _("Error, password not changed !")
        try:
            if request.env['res.users'].change_password(old_password, new_password):
                return {'new_password':new_password}
        except AccessDenied as e:
            msg = e.args[0]
            if msg == AccessDenied().args[0]:
                msg = _('The old password you provided is incorrect, your password was not changed.')
        except UserError as e:
            msg = e.args[0]
        return {'title': _('Change Password'), 'error': msg}

    @http.route('/gui_api/session/get_lang_list', type='json', auth="none")
    def get_lang_list(self):
        try:
            return dispatch_rpc('db', 'list_lang', []) or []
        except Exception as e:
            return {"error": e, "title": _("Languages")}

    @http.route('/gui_api/session/check', type='json', auth="user")
    def check(self):
        request.session.check_security()
        return None

    @http.route('/gui_api/session/destroy', type='json', auth="user")
    def destroy(self):
        request.session.logout()

    @http.route('/gui_api/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)

##### gui_api model ##########
    def __init__(self):
        self._model = "ir.model"

    @http.route('/gui_api/product', type='json', auth='user', methods=["GET"], csrf=False)
    def call_product_list(self, **post):
        model='product.product'
        function='get_product_list'
        args = []
        kwargs = {}
        model = request.env[model]
        result = getattr(model, function)(*args, **kwargs)
        return result

    @http.route(_routes, type="json", auth="none", methods=["GET"], csrf=False)
    def get(self, model=None, id=None, **payload):
        try:
            ioc_name = model
            model = request.env[self._model].search([("model", "=", model)], limit=1)
            if model:
                domain, fields, offset, limit, order = extract_arguments(**payload)
                data = request.env[model.model].search_read(
                    domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                )

                if id:
                    domain = [("id", "=", int(id))]
                    data = request.env[model.model].search_read(
                        domain=domain, fields=fields, offset=offset, limit=limit, order=order,
                    )
                if data:
                    return valid_response(data)
                else:
                    return valid_response(data)
            return invalid_response(
                "invalid object model", "The model %s is not available in the registry." % ioc_name,
            )
        except AccessError as e:

            return invalid_response("Access error", "Error: %s" % e.name)
