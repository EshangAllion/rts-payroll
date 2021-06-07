from odoo import models, api, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    profitability = fields.Float(string="Profitability (%)", store=True)

    def action_invoice_open(self):
        """this function will show the invoice wise profitability"""

        total_cost = 0  # initialize invoice total cost is  0
        selling_price = 0  # initialize total selling price is  0
        res = super(AccountInvoice, self).action_invoice_open()  # assigning a super class to the object
        self.profitability = 0  # initialize profitability is  0

        for line in self.invoice_line_ids:  # rotate every invoice line
            total_cost += line.quantity * line.product_id.standard_price  # calculate the total cost
            selling_price += line.quantity * line.price_unit  # calculate the total selling price
        profit = selling_price - total_cost  # calculate the profit of invoice and assigning to the object
        self.profitability += profit / selling_price * 100  # calculate the total profitability as a %

        return res  #return super class