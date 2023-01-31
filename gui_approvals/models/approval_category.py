import base64
from pickle import FALSE

from odoo import api, fields, models, tools, _
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'
    _description = 'Approval Category'

    approval_lines = fields.One2many('approval.category.line','approval_categ_id',string='Approval Line')
    order_type_id = fields.Many2one(string='Order Type', comodel_name='sdt.order.type')

class ApprovalCategoryLine(models.Model):
    _name = 'approval.category.line'
    _description = 'Multi Staging Approvals'
    _order = 'sequence'

    _check_company_auto = True

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string="Description", translate=True, required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', copy=False,
        required=True, index=True, default=lambda s: s.env.company)
    sequence = fields.Integer(string="Sequence")
    approval_categ_id = fields.Many2one('approval.category',string='Approval Category')
    user_ids = fields.Many2many('res.users', string="Approvers",
        check_company=True, domain="[('company_ids', 'in', company_id)]")
    minimum_amount = fields.Monetary('Minimum Amount',copy=False)
    maximum_amount = fields.Monetary('Maximum Amount',copy=False)
    maximum_amount_limit = fields.Monetary('Maximum Amount Limit',copy=False)
    maximum_ageing = fields.Integer('Maximum Ageing',copy=False)
    currency_id = fields.Many2one('res.currency', string="Currency", default=_default_currency)


