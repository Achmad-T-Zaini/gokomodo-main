from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    terbilang = fields.Text(string='Terbilang', copy=False, store=False, compute="_compute_terbilang")
    sales_person_employee = fields.Many2one('hr.employee',string='Sales Person', 
        domain="[('sales_team_id', '=', team_id)]",)


    @api.depends('amount_total')
    def _compute_terbilang(self):
        self.ensure_one()
        self.update({'terbilang': False})
        if self.amount_total and self.amount_total>0:
            self.update({'terbilang': self.env['account.terbilang'].terbilang(self.amount_total) + self.currency_id.currency_unit_label})

    @api.onchange('team_id')
    def onchange_team_id(self):
        team_domain = False
        if self.team_id:
            sales_employee = self.env['hr.employee'].search([('sales_team_id','=',self.team_id.id)])
            team_domain = {'domain': {'sales_person_employee': [('id', 'in', sales_employee.ids)]}}
            self.sales_person_employee = False
        return team_domain

    @api.onchange('sales_person_employee')
    def onchange_sales_person_employee(self):
        if self.sales_person_employee and self.sales_person_employee.user_id:
            self.invoice_user_id = self.sales_person_employee.user_id.id
        elif self.sales_person_employee:
            raise UserError(_("Employee %s doesn't have user_id, please contact Adminstrator")%(self.sales_person_employee.name,))

    @api.model
    def create(self, vals):
        if vals.get('invoice_user_id',False):
            employee = self.env['hr.employee'].search([('user_id','=',vals['invoice_user_id'])])
            if employee.user_id:
                vals['sales_person_employee'] = employee.id
            else:
                vals['invoice_user_id']=False

        return super(AccountMove, self).create(vals)
