from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from num2words import num2words

class AccountTerbilang(models.Model):
    _name = "account.terbilang"
    _description = "Amount Terbilang"

    name = fields.Char(string='Amount Words', required=True, copy=False, Store=True)
    bilang = fields.Char(string='Translation', copy=False, Store=True)

    def terbilang(self,amount):
        nilai = num2words(amount)
        account_terbilang = self.env['account.terbilang'].search([('id','!=',False)])
        for line in account_terbilang:
            if line.bilang:
                nilai = nilai.replace(line.name,line.bilang)
            else:
                nilai = nilai.replace(line.name,'')
        if 1000<=amount<=1999:
                nilai = nilai.replace('Satu Ribu','Seribu')
        nilai = nilai.replace('-',' ')
        nilai = nilai.replace('and','')
        nilai = nilai.replace(',','')
        nilai = nilai.replace('  ',' ')
#        nilai = num2words(amount)

        return nilai + " "

