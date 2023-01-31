import base64
from pickle import FALSE

from odoo import api, fields, models, tools, _
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_cancel(self):
        for order in self:
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel the related vendor bills."))

        approvals = self.env['approval.request'].search([('purchase_order_id','=',self.id)])
        if approvals:
            for approval in approvals:
                approval.write({'request_status': 'cancel'})
                approval.message_post(body='Purchase Order Cancelled')
        self.write({'state': 'cancel', 'mail_reminder_confirmed': False})

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        inv = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        inv.button_cancel()
        approvals = self.env['approval.request'].search([('sale_id','=',self.id)])
        if approvals:
            for approval in approvals:
                approval.write({'request_status': 'cancel'})
                approval.message_post(body='Sales Order Cancelled')
        return self.write({'state': 'cancel'})

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())


        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)


        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return 

    def _get_forbidden_state_confirm(self):
        return {'done', 'cancel'}
#        return {'cancel'}

    def _prepare_product_line(self,line_id,approvals_id):
        return {
                    'approval_request_id': approvals_id.id,
                    'product_id': line_id.product_id.id,
                    'description': line_id.name,
                    'quantity': line_id.product_uom_qty,
                    'product_uom_id': line_id.product_uom.id,
                    'sale_line_id': line_id.id,
                }

    def open_approvals_all_inone(self):
        self.ensure_one()

        for order in self:
            sql_query="""select count(1) from ir_attachment where res_model='sale.order' and res_id=%s
                """
            self.env.cr.execute(sql_query,(order.id,))
            cek_attachment=self.env.cr.fetchone()[0] or 0
            if cek_attachment == 0:
                raise UserError(_(
                    "Attachment Not Found,  \n"
                    "Please input Attachment (%s).") % (order.name))
                    
        self.is_all_inone = True
        approval_fm_c = self.env['approval.category'].search([('approval_fm','=',True),('corporate','=',True)])
        approvals_pm_c = self.env['approval.category'].search([('approval_cm','=',True),('corporate','=',True)])
        
        approval_fm_r = self.env['approval.category'].search([('approval_fm','=',True),('retail','=',True)])
        approvals_pm_r = self.env['approval.category'].search([('approval_cm','=',True),('retail','=',True)])

        if self.order_type_id.name == 'Corporate' :
            self['approval_category_fm_id'] = approval_fm_c.id
            self['approval_category_cm_id'] = approvals_pm_c.id

        if self.order_type_id.name == 'Retail' :
            self['approval_category_fm_id'] = approval_fm_r.id
            self['approval_category_cm_id'] = approvals_pm_r.id

        if self.partner_id.parent_id:
            partner = self.partner_id.parent_id
        else:
            partner = self.partner_id

        # terbentuk jika credit limit > 0.0 
        number_day = self.env['account.payment.term.line'].search([('payment_id','=',self.payment_term_id.id)])
        if self.approval_category_fm_id and partner.credit_limit > 0.0 : 
            approvals_id = self.env['approval.request'].sudo().create({
                'name':'Approval/FM-'+self.name,
                'date' : fields.Datetime.now(),
                'reference':self.name,
                'category_id' : self.approval_category_fm_id.id,
                'sale_id' : self.id,
                'request_owner_id' : self.env.uid,
                'request_status' : 'pending',
                'over_limit' : self.over_limit,
                'amount':self.amount_total,
            })
            for line_id in self.order_line:
                if not line_id.is_downpayment:
                    vals = self._prepare_product_line(line_id,approvals_id)
                    self.env['approval.product.line'].create(vals)
            self.state_approval_fm = 'waiting'
            approval= []
            for i in approvals_id.category_id.user_ids:
                approval.append(
                    (0,0, {'user_id': i.id})
                )
            approvals_id.write({
            'approver_ids': approval
            })
            approvals_id.action_confirm()
            # FM terbentuk jika credit limit == 0.0 dan number of day > 0
        elif self.approval_category_fm_id and partner.credit_limit == 0.0 :
            if number_day.days > 0 : 
                approvals_id = self.env['approval.request'].sudo().create({
                    'name':'Approval/FM-'+self.name,
                    'date' : fields.Datetime.now(),
                    'reference':self.name,
                    'category_id' : self.approval_category_fm_id.id,
                    'sale_id' : self.id,
                    'request_owner_id' : self.env.uid,
                    'request_status' : 'pending',
                    'over_limit' : self.over_limit,
                    'amount':self.amount_total,
                })
                for line_id in self.order_line:
                    if not line_id.is_downpayment:
                        vals = self._prepare_product_line(line_id,approvals_id)
                        self.env['approval.product.line'].create(vals)
                self.state_approval_fm = 'waiting'
                approval= []
                for i in approvals_id.category_id.user_ids:
                    approval.append(
                        (0,0, {'user_id': i.id})
                    )
                approvals_id.write({
                'approver_ids': approval
                })
                approvals_id.action_confirm()
            else :
                self.state_approval_fm = 'cancel'
        else :
            self.state_approval_fm = 'cancel'

        if self.approval_category_cm_id :
            approvals_id = self.env['approval.request'].sudo().create({
                'name':'Approval/CM-'+self.name,
                'date' : fields.Datetime.now(),
                'reference':self.name,
                'category_id' : self.approval_category_cm_id.id,
                'sale_id' : self.id,
                'request_owner_id' : self.env.uid,
                'request_status' : 'pending',
                'over_limit' : self.over_limit,
                'amount':self.amount_total,
            })
            for line_id in self.order_line:
                if not line_id.is_downpayment:
                    vals = self._prepare_product_line(line_id,approvals_id)
                    self.env['approval.product.line'].create(vals)
            self.state_approval_cm = 'waiting'
            approval= []
            for i in approvals_id.category_id.user_ids:
                approval.append(
                    (0,0, {'user_id': i.id})
                )
            approvals_id.write({
            'approver_ids': approval
            })
            approvals_id.action_confirm()


