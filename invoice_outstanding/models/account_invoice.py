from odoo import models, api, fields, _
import operator


class AccountInvoiceInherit(models.Model):
    _inherit = 'account.move'

    overdue_amount = fields.Monetary(compute='_compute_overdue_amount', string='Outstanding Amount', search='_set_overdue_amount')
    # stored_overdue_amount = fields.Monetary(compute='_compute_stored_overdue_amount', string='Outstanding Amount', default=0.0)

    def _compute_overdue_amount(self):
        """Calculating Real outstanding by excluding all draft cheque payments"""
        for line in self:
            line.overdue_amount = 0
            if line.type == 'out_invoice':
                payments_obj = self.env['account.payment'].search([('partner_id', '=', line.partner_id.id), ('state', '=', 'posted'), ('bulk_payment_id.state', 'in', ['cheque_on_hand', 'deposited']),
                     ('payment_type_name', '=', 'Cheque')])
                payments = payments_obj.filtered(lambda x: line.id in x.reconciled_invoice_ids.ids)
                line.overdue_amount = line.amount_residual
                if payments:
                    total = sum(item.amount for item in payments)
                    line.overdue_amount += total
                else:
                    line.overdue_amount = line.amount_residual
            else:
                line.overdue_amount = 0

    def _compute_stored_overdue_amount(self):
        """Calculating Real outstanding by excluding all draft cheque payments"""
        for line in self:
            # line.stored_overdue_amount = 0
            if line.type == 'out_invoice':
                payments = self.env['account.payment'].search(
                    [('reconciled_invoice_ids', 'in', line.id), ('state', '=', 'posted'), ('bulk_payment_id', '!=', False),
                     ('payment_type_name', '=', 'Cheque')])
                line.overdue_amount = line.amount_residual
                if payments:
                    filtered_payments = payments.filtered(
                        lambda x: x.bulk_payment_id.state in ['cheque_on_hand', 'deposited'])
                    if filtered_payments:
                        total = 0
                        for item in filtered_payments:
                            if line.id in item.reconciled_invoice_ids.ids:
                                total += item.amount
                        line.overdue_amount += total
                        # line.stored_overdue_amount += total

    def _set_overdue_amount(self, operator, value):
        """search function for overdue_amount"""
        all_invoice = self.search([('type', '=', 'out_invoice')])
        if operator == '>':
            recs = all_invoice.filtered(lambda x: x.overdue_amount > value)
        elif operator == '<':
            recs = all_invoice.filtered(lambda x: x.overdue_amount < value)
        elif operator == '<=':
            recs = all_invoice.filtered(lambda x: x.overdue_amount <= value)
        elif operator == '>=':
            recs = all_invoice.filtered(lambda x: x.overdue_amount >= value)
        else:
            recs = all_invoice.filtered(lambda x: x.overdue_amount == value)
        return [('id', 'in', [x.id for x in recs])]


class InheritResPartner(models.Model):

    _inherit = 'res.partner'

    total_outstanding = fields.Float(compute='_compute_total_outstanding', string='Total Outstanding')

    def _compute_total_outstanding(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        for id in self:
            return_checks_total = sum((return_check.overdue_amount) for return_check in
                                      self.env['returned.checks'].search([('partner_id', '=', id.id)]))
            invoices_total = sum(invoice.overdue_amount for invoice in self.env['account.move'].search(
                [('partner_id', '=', id.id), ('state', 'in', ['posted']), ('type', '=', 'out_invoice')]))
            id.total_outstanding = return_checks_total + invoices_total




