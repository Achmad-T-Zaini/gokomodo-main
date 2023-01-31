# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Gokomodo Inventory Custom',
    'version': '14.0.2.0.0',
    'license': 'AGPL-3',
    'category': 'Inventory',
    'author': 'Achmad T. Zaini ',
    'depends': [
        'base', 'web', 'stock', 'product',
        'account', 'account_asset',
        'sdt_sale_order_gui',
    ],
    'data': [
        'security/warehouse_picking_type_security.xml',
        'views/gui_partner_views.xml',
        'views/gui_product_template_views.xml',
        'views/gui_stock_location_route_views.xml',
        'report/surat_jalan.xml',
        'report/inventory_scm_report_views.xml',
    ],
    'installable': True,
    'application': False,
}
