from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.stock.models.product import Product as OriginalProduct


def _compute_quantities(self):
    products = self.filtered(lambda p: p.type != 'service')
    res = products._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
    for product in products:
        if product.sh_is_bundle:
            raise UserError(_('PBundle %s')%(product.name))
        product.qty_available = res[product.id]['qty_available']
        product.incoming_qty = res[product.id]['incoming_qty']
        product.outgoing_qty = res[product.id]['outgoing_qty']
        product.virtual_available = res[product.id]['virtual_available']
        product.free_qty = res[product.id]['free_qty']
        # Services need to be set with 0.0 for all quantities
    services = self - products
    services.qty_available = 0.0
    services.incoming_qty = 0.0
    services.outgoing_qty = 0.0
    services.virtual_available = 0.0
    services.free_qty = 0.0
    # Insert the original code with your changes here

OriginalProduct._compute_quantities = _compute_quantities