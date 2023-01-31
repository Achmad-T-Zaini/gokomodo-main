# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"


    @api.model
    def _prepare_purchase_order_line(self, po, item):
        if not item.product_id:
            raise UserError(_("Please select a product for all lines"))
        product = item.product_id

        # Keep the standard product UOM for purchase order so we should
        # convert the product quantity to this UOM
        qty = item.product_uom_id._compute_quantity(
            item.product_qty, product.uom_po_id or product.uom_id
        )
        # Suggest the supplier min qty as it's done in Odoo core
        min_qty = item.line_id._get_supplier_min_qty(product, po.partner_id)
        qty = max(qty, min_qty)
        date_required = item.line_id.date_required
        vals = {
            "sale_order_id": item.line_id.sale_line_id.order_id.id,
            "sale_line_id": item.line_id.sale_line_id.id,
            "name": product.name,
            "order_id": po.id,
            "product_id": product.id,
            "product_uom": product.uom_po_id.id or product.uom_id.id,
            "price_unit": 0.0,
            "price_befdisc": item.line_id.estimated_cost,
            "product_qty": qty,
            "account_analytic_id": item.line_id.analytic_account_id.id,
            "purchase_request_lines": [(4, item.line_id.id)],
            "date_planned": datetime(
                date_required.year, date_required.month, date_required.day
            ),
            "move_dest_ids": [(4, x.id) for x in item.line_id.move_dest_ids],
        }
#        raise UserError(_('PR %s')%(vals,))
        self._execute_purchase_line_onchange(vals)
        return vals
