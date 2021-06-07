# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import json


MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

MAP_INVOICE_TYPE_PAYMENT_TYPE = {
    'out_invoice': 'inbound',
    'out_refund': 'outbound',
    'in_invoice': 'outbound',
    'in_refund': 'inbound',
}

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class BulkPayment(models.Model):
    _name = "account.bulk.payment"

    bulk_payment_lines = fields.One2many(string='Payment Lines', comodel_name='account.bulk.payment.line',
                                         inverse_name='bulk_payment_id')
    payment_ids = fields.One2many(string='Payments', comodel_name='account.payment',
                                  inverse_name='bulk_payment_id')

    name = fields.Char(readonly=True, copy=False)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type',
                                    readonly=True, copy=False)
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note'),
    ])
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, copy=False)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], readonly=True, copy=False)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', readonly=True, copy=False)
    payment_method_code = fields.Char(related='payment_method_id.code', readonly=True, copy=False)
    check_manual_sequencing = fields.Boolean(related='journal_id.check_manual_sequencing', readonly=True, copy=False)
    manual_check_number = fields.Char(string="Check Number", readonly=True, copy=False)
    check_number = fields.Integer(string="Check Number", readonly=True, copy=False)

    lines_total_amount = fields.Monetary(string='Payment Amount', readonly=True, copy=False)
    lines_total_amount_in_words = fields.Char(string="Amount in Words", readonly=True, copy=False)

    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, copy=False)
    payment_date = fields.Date(string='Payment Date', readonly=True, copy=False)
    communication = fields.Char(string='Memo')
    journal_id = fields.Many2one(comodel_name='account.journal', string='Payment Journal', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True)

    cheque_no = fields.Char(string="Cheque/Slip No.")
    cheque_date = fields.Date(string='Cheque/Slip Date', default=fields.Date.context_today)
    payment_type_name = fields.Char(related='payment_method_id.name')
    deposited_account_no = fields.Many2one('res.partner.bank', string="Deposited Bank Account")
    deposited_date = fields.Date(string='Deposited Date', default=fields.Date.context_today)
    return_cheque = fields.Boolean(string="Return Cheque")
    deposited_bank_branch = fields.Many2one('res.country.state', string="Deposited Bank Branch",
                                            related='deposited_account_no.bank_id.state')
    deposited_bank = fields.Many2one('res.bank', string="Deposited Bank", related='deposited_account_no.bank_id')
    account_no = fields.Many2one('res.partner.bank', string="Bank Account", related='journal_id.bank_account_id')
    bank = fields.Many2one('res.bank', string="Bank")
    is_returned = fields.Boolean('Is Returned', default=False)
    receipt_no = fields.Many2one('receipts.numbers', string="Receipt No")

    def compute_lines_total_amount(self):
        """Updating total Amount"""
        total = 0
        for line in self.payment_ids.filtered(lambda x: x.state not in ['draft', 'cancelled']):
            total += line.amount
        self.write({
            "lines_total_amount": total,
            "lines_total_amount_in_words": self.currency_id.amount_to_text(total)
        })

    # def open_journal_entries(self):
    #     """
    #     return action for open relevant bulk payment form view
    #     """
    #     for lines in self.payment_ids:
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'account.bulk.payment',
    #         'target': 'current',
    #         'domain': "None"
    #     }

class BulkPaymentLine(models.Model):
    _name = "account.bulk.payment.line"

    bulk_payment_id = fields.Many2one(string='Bulk Payment', comodel_name='account.bulk.payment', readonly=True, copy=False)
    invoice_id = fields.Many2one(string='Invoice/Vendor Bill', comodel_name='account.move', readonly=True, copy=False)
    invoice_total = fields.Monetary(string='Total Invoiced Amount', readonly=True, copy=False, related='invoice_id.amount_total')
    invoice_due = fields.Monetary(string='Invoice Residual Amount', readonly=True, copy=False, related='invoice_id.amount_residual')
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency',  readonly=True, copy=False)
    amount = fields.Monetary(string='Payment Amount', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', related='bulk_payment_id.journal_id.company_id', string='Company', readonly=True, store=True)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    bulk_payment_id = fields.Many2one(string='Bulk Payment', comodel_name='account.bulk.payment', copy=False)
    manual_check_number = fields.Char(string="Check Number")
    cheque_no = fields.Char(string="Cheque/Slip No.")
    cheque_date = fields.Date(string='Cheque/Slip Date', default=fields.Date.context_today)
    payment_type_name = fields.Char(related='payment_method_id.name')
    deposited_account_no = fields.Many2one('res.partner.bank', string="Deposited Bank Account")
    deposited_date = fields.Date(string='Deposited Date', default=fields.Date.context_today)
    return_cheque = fields.Boolean(string="Return Cheque")
    deposited_bank_branch = fields.Many2one('res.country.state', string="Deposited Bank Branch")
    deposited_bank = fields.Many2one('res.bank', string="Deposited Bank")
    account_no = fields.Many2one('res.partner.bank', string="Bank Account")
    bank = fields.Many2one('res.bank', string="Bank")
    receipt_no = fields.Many2one('receipts.numbers', string="Receipt No")

    @api.depends('move_line_ids.matched_debit_ids', 'move_line_ids.matched_credit_ids')
    def _compute_reconciled_invoice_ids(self):
        """Inheriting core feature to calculate reconciled invoice"""
        for record in self:
            reconciled_moves = record.move_line_ids.mapped('matched_debit_ids.debit_move_id.move_id') \
                               + record.move_line_ids.mapped('matched_credit_ids.credit_move_id.move_id')
            record.reconciled_invoice_ids = reconciled_moves.filtered(lambda move: move.is_invoice())
            record.has_invoices = bool(record.reconciled_invoice_ids)
            record.reconciled_invoices_count = len(record.reconciled_invoice_ids)
            if record.reconciled_invoice_ids:
                for line in record.bulk_payment_id.bulk_payment_lines.filtered(
                        lambda x: x.invoice_id.id in record.reconciled_invoice_ids.ids):
                    amount = self.get_payment_of_invoice(json.loads(line.invoice_id.invoice_payments_widget).get('content'), record)
                    line.write({
                        "amount": amount
                    })

    def get_payment_of_invoice(self, content, payment):
        for item in content:
            if item.get('account_payment_id') == payment.id:
                return item.get('amount')

    def open_bulk_payment(self):
        """
        return action for open relevant bulk payment form view
        """
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.bulk_payment_id.id,
            'res_model': 'account.bulk.payment',
            'target': 'current',
        }

    def action_register_payment(self):
        """Function that loads register payments wizard"""
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_account_payment_form_multi').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def write(self, vals):
        """Updating bulkpayment values"""
        return_obj = super(AccountPayment, self).write(vals)
        if self.bulk_payment_id:
            self.bulk_payment_id.compute_lines_total_amount()
            for line in self.bulk_payment_id.bulk_payment_lines.filtered(lambda x: x.invoice_id.id in self.invoice_ids.ids):
                line.write({
                    "amount": self.amount
                })
        return return_obj


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _enable_check_printing_inbound_on_bank_journals(self):
        """ Enables check printing payment method .
            Called upon module installation via data file.
        """
        check_printing = self.env.ref('bulk_payment.account_payment_method_check_bulk')
        bank_journals = self.search([('type', '=', 'bank')])
        for bank_journal in bank_journals:
            bank_journal.write({
                'inbound_payment_method_ids': [(4, check_printing.id, None)],
            })


class ReceiptNumbers(models.Model):
    _name = 'receipts.numbers'

    name = fields.Char(string="Name", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Name already exists !"),
    ]