
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class OrderType(models.Model):
    _inherit = "sdt.order.type"

    sales_order_type = fields.Selection(string='Sales Type',
        selection=[
            ('Corporate', 'Corporate'),
            ('Retail', 'Retail'),
            ('Jasa', 'Jasa'),
            ('Subscription', 'Subscription'),
            ],
        default="Corporate",copy=False, store=True)
