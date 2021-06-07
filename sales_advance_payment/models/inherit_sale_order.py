from odoo import fields, models, api
from odoo.exceptions import UserError


class InheritSalesOrder(models.Model):
    _inherit = 'sale.order'

    advance_payment_ids = fields.Many2many('account.payment', string="Advance Payments")
    advance_payments_total = fields.Monetary('Payments', compute='_get_advance_payments_total')

    def _get_advance_payments_total(self):
        """Get advance payments total"""
        for line in self:
            line.advance_payments_total = sum(payment.amount for payment in line.advance_payment_ids)

    def open_advance_payments(self):
        """
        return action for open relevant bulk payment form view
        """
        return {
            'name': 'Advance Payments',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_id': self.advance_payment_ids.ids,
            'domain': [('id', 'in', self.advance_payment_ids.ids)],
            'res_model': 'account.payment',
            'target': 'current',
        }

    def _prepare_invoice(self,):
        """inheriting function that sends data to invoice"""
        invoice_vals = super(InheritSalesOrder, self)._prepare_invoice()
        invoice_vals.update({
            'total_advance': self.advance_payments_total,
        })
        return invoice_vals


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    total_paid_amount = fields.Monetary(string="Total Paid Amount")
    total_advance = fields.Monetary(string="Total Paid Amount")
    balance = fields.Monetary(string="Balance")


class InheritPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    paying_amount = fields.Float("Paying Amount")
    balance = fields.Float("Balance", compute='_get_balance')

    @api.depends('paying_amount', 'payment_lines.amount')
    def _get_balance(self):
        """Getting balance"""
        for line in self:
            line.balance = line.paying_amount - line.lines_total_amount

    def create_payments(self):
        """Create payments function overidden"""
        invoice = self.env['account.move'].browse(self._context.get('active_ids'))
        if self.balance < 0:
            raise UserError("Balance cannot be 0.")
        invoice.write({
            'total_paid_amount': (self.paying_amount),
            'balance': self.balance,
        })
        return super(InheritPaymentRegister, self).create_payments()