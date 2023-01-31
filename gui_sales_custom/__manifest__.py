# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Gokomodo Sales Custom v2',
    'version': '14.0.2.0.0',
    'license': 'AGPL-3',
    'category': 'Sales',
    'author': 'Achmad T. Zaini ',
    'depends': [
        'base', 'hr', 'crm', 'sale','account', 
#        'purchase_request', 'form_standard_odoo',
#        'sdt_report_sales', 'sdt_udf_gui',
#        'web', 'stock', 'product',
        'sdt_sale_order_gui', 'sale_enterprise'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/gui_sale_order_views.xml',
        'views/gui_sale_order_type_views.xml',
        'views/gui_sales_team_views.xml',
        'views/gui_account_terbilang_views.xml',
#        'views/gui_purchase_views.xml',
        'views/gui_account_move_views.xml',
        'report/sale_report_templates.xml',
        'report/sdt_standard_sales_invoice.xml',
        'report/sdt_standard_sales_order.xml',
        'report/sales_report_commercial.xml',
        'report/sales_commercial_report_views.xml',
    ],
    'installable': True,
    'application': False,
}
