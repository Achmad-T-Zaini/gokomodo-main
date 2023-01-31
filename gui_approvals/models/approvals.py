# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import hashlib
import json


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    amount_untaxed = fields.Monetary(string='Untaxed Amount', related="sale_id.amount_untaxed" )
    amount_tax = fields.Monetary(string='Taxes', related="sale_id.amount_tax")
    amount_total = fields.Monetary(string='Total', related="sale_id.amount_total")
    notes = fields.Text(string='Note')
    currency_id = fields.Many2one('res.currency', string="Currency", default=_default_currency)
    discount = fields.Monetary(string="Discount", related="sale_id.discount")
    amount_without_discount_tax = fields.Monetary(string="Amount without discount and tax", related="sale_id.amount_without_discount_tax")
    product_so_line_ids = fields.One2many('approval.product.line', 'approval_request_id', check_company=True)

    def action_approve(self, approver=None):

        if self.category_id.purchase_request == True :
            self.purchase_request_id.approve = True
#            self.purchase_request_id.button_to_approve()
            self.purchase_request_id.button_approved()

        if self.category_id.approval_fm == True :
            self.sale_id.state_approval_fm = 'approved'
            self.sale_id.is_approvals = True

            if self.sale_id.partner_id.parent_id:
                partner = self.sale_id.partner_id.parent_id                
            else:
                partner = self.sale_id.partner_id

            number_day = self.env['account.payment.term.line'].search([('payment_id','=',self.sale_id.payment_term_id.id)])
            

            if self.sale_id.approval_category_fm_id and partner.credit_limit > 0.0 :
                if self.sale_id.state_approval_fm == 'approved' and self.sale_id.state_approval_cm == 'approved':
                    self.sale_id.action_confirm()
            elif self.sale_id.approval_category_fm_id and partner.credit_limit == 0.0 :
                if number_day.days > 0 : 
                    if self.sale_id.state_approval_fm == 'approved' and self.sale_id.state_approval_cm == 'approved':
                        self.sale_id.action_confirm()
                else :
                    self.sale_id.action_confirm()
            else :
                self.sale_id.action_confirm()
        
        if self.category_id.approval_cm == True :
            self.sale_id.state_approval_cm = 'approved'
            self.sale_id.is_approvals = True

            if self.sale_id.partner_id.parent_id:
                partner = self.sale_id.partner_id.parent_id                
            else:
                partner = self.sale_id.partner_id

            number_day = self.env['account.payment.term.line'].search([('payment_id','=',self.sale_id.payment_term_id.id)])

            if self.sale_id.approval_category_fm_id and partner.credit_limit > 0.0 :
                if self.sale_id.state_approval_fm == 'approved' and self.sale_id.state_approval_cm == 'approved':
                    self.sale_id.action_confirm()
            elif self.sale_id.approval_category_fm_id and partner.credit_limit == 0.0 :
                if number_day.days > 0 : 
                    if self.sale_id.state_approval_fm == 'approved' and self.sale_id.state_approval_cm == 'approved':
                        self.sale_id.action_confirm()
                else :
                    self.sale_id.action_confirm()
            else :
                self.sale_id.action_confirm()

        if self.sale_id:
            pr_id = self.env['purchase.request'].search([('sale_id','=',self.sale_id.id)])
            if pr_id:
                self.sale_id.write({'purchase_request_id': pr_id.id,})

        if self.category_id.purchase_order == True :
            self.purchase_order_id.state_approval = 'approved'
            self.purchase_order_id.button_confirm()

        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approver.write({'status': 'approved'})
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
    
    def action_cancel(self):
        return {
                'name': 'Cancel Reason Form',
                'type': 'ir.actions.act_window',
                'res_model': 'approval.request.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {"default_approval_request_id": self.id,
                            "default_state": "cancel"}
                  }

    def action_refuse(self):
        return {
                'name': 'Refuse Reason Form',
                'type': 'ir.actions.act_window',
                'res_model': 'approval.request.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {"default_approval_request_id": self.id,
                            "default_state": "refuse"}
                  }

class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    sale_line_id = fields.Many2one("sale.order.line", string='Order Line')
    cost_market = fields.Float(string='Cost Market', related="sale_line_id.cost_market")
    price_margin = fields.Float(string='Margin %', related="sale_line_id.price_margin")
    standard_price = fields.Float(string="Cost Product", related="sale_line_id.standard_price")
    price_margin_percentage = fields.Float(string="Margin Product (%)", related="sale_line_id.price_margin_percentage")
    price_unit = fields.Float('Unit Price', related="sale_line_id.price_unit")
    price_subtotal = fields.Monetary(string='Subtotal', related="sale_line_id.price_subtotal" )
    currency_id = fields.Many2one('res.currency', string="Currency", default=_default_currency)
    tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    discount_amount = fields.Float(string="Discount amount", related="sale_line_id.discount_amount")
    discount_show = fields.Float(string="Discount (%)", related="sale_line_id.discount_show")

    @api.model
    def create(self, vals):
        res = super(ApprovalProductLine, self).create(vals)
        sol = False
        if vals.get('sale_line_id',False):
            sol = self.env['sale.order.line'].browse(vals['sale_line_id'])
            res.tax_id = sol.tax_id.ids 
        return res

class approval_cancel_wizard(models.TransientModel):
    _name = 'approval.request.wizard'
    _description = 'Approval Request Cancel Wizard'

    message = fields.Text(string="Reasons / Note")
    approval_request_id = fields.Many2one('approval.request', string='Request ID')
    state = fields.Selection([
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled'),
    ], string="Order Status", readonly=True)


    def action_confirm(self, approver=None):
        if self.state=="cancel":
            notes = self.approval_request_id.name + " Cancelled : " + self.message
            if self.approval_request_id.sale_id:
                self.approval_request_id.sale_id.message_post(body=notes)
                self.approval_request_id.sale_id.write({"state": "cancel"})
            elif self.approval_request_id.purchase_order_id:
                self.approval_request_id.purchase_order_id.message_post(body=notes)
                self.approval_request_id.purchase_order_id.write({"state": "cancel"})
            elif self.approval_request_id.purchase_request_id:
                self.approval_request_id.purchase_request_id.message_post(body=notes)
                self.approval_request_id.purchase_request_id.write({"state": "rejected"})

            self.approval_request_id.sudo()._get_user_approval_activities(user=self.env.user).unlink()
            self.approval_request_id.mapped('approver_ids').write({'status': 'cancel'})
        elif self.state=="refuse":
            if not isinstance(approver, models.BaseModel):
                approver = self.approval_request_id.mapped('approver_ids').filtered(
                    lambda approver: approver.user_id == self.env.user
                )
            if self.approval_request_id.category_id.approval_fm:
                self.approval_request_id.sale_id.state_approval_fm = 'cancel'
                self.approval_request_id.sale_id.action_cancel()
        
            if self.approval_request_id.category_id.approval_cm:
                self.approval_request_id.sale_id.state_approval_cm = 'cancel'
                self.approval_request_id.sale_id.action_cancel()
        
            if self.approval_request_id.purchase_request_id:
                self.approval_request_id.purchase_request_id.button_rejected()
        
            if self.approval_request_id.category_id.purchase_order:
                self.approval_request_id.purchase_order_id.state_approval = 'draft'
                self.approval_request_id.purchase_order_id.button_cancel()

            notes = self.approval_request_id.name + " Refused : " + self.message
            if self.approval_request_id.sale_id:
                self.approval_request_id.sale_id.message_post(body=notes)
            elif self.approval_request_id.purchase_order_id:
                self.approval_request_id.purchase_order_id.message_post(body=notes)
            elif self.approval_request_id.purchase_request_id:
                self.approval_request_id.purchase_request_id.message_post(body=notes)

            approver.write({'status': 'refused'})
            res = super(ApprovalRequest, self.approval_request_id).action_refuse()
            self.approval_request_id.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()
        self.approval_request_id.write({"notes": notes})
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
              }
