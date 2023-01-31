# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Gokomodo Purchase Custom',
    'version': '14.0.2.0.0',
    'license': 'AGPL-3',
    'category': 'Purchase',
    'author': 'Achmad T. Zaini ',
    'depends': [
        'base', 'sale', 'account', 'purchase',
        'purchase_request', 'form_standard_odoo', 
        'sdt_udf_gui', 'purchase_discount',
    ],
    'data': [
        'report/gui_purchase_order_report.xml',
        'report/gui_purchase_reports.xml',
        'views/gui_purchase_views.xml',
    ],
    'installable': True,
    'application': False,
}
