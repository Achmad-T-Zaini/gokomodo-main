# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Gokomodo Finance Custom',
    'version': '14.0.2.0.0',
    'license': 'AGPL-3',
    'category': 'Accounting',
    'author': 'Achmad T. Zaini ',
    'depends': [
        'base', 'account', 'account_asset',
        'sdt_sale_order_gui',
    ],
    'data': [
        'report/inventory_transit_report_views.xml',
#        'report/sale_report_templates.xml',
        'views/gui_intransit_report_menu.xml'
    ],
    'installable': True,
    'application': False,
}
