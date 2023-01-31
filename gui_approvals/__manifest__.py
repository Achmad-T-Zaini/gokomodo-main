# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Gokomodo Approvals Custom',
    'version': '14.0.2.0.0',
    'license': 'AGPL-3',
    'category': 'Approvals',
    'author': 'Achmad T. Zaini ',
    'depends': [
        'base', 'approvals', 'sdt_approvals_gui', 'sale',
        'sdt_discount_value',
    ],
    'data': [
        'views/gui_approval_request_views.xml',
        'security/ir.model.access.csv',
#        'views/gui_approval_category_views.xml',
    ],
    'installable': True,
    'application': False,
}
