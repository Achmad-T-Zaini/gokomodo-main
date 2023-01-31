# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Gokomodo Resource Customs',
    'Author': 'Achmad T. Zaini',
    'Company' : 'PT. Gokomodo Uniti Indonesia+',
    'version': '1.1',
    'category': 'Wilayah',
    'summary': 'Wilayah',
    'description': """
        This module contains all the common features on Resources.
        penambahan field city_id
    """,
    'depends': [
        "base", "contacts", "resource", "account", "purchase",
        ],
    'data': [
        'security/wilayah_security.xml',
        'security/gui_groups.xml',
        'security/ir.model.access.csv',
        'views/res_country_views.xml',
        'views/gui_partner_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
