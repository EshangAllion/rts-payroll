from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import float_compare
import json


class InheritAccountBulkPayment(models.Model):
    _inherit = 'account.bulk.payment'

    state = fields.Selection([('collected', 'Payment Collected'), ('cheque_on_hand', 'Cheque on Hand'), ('deposited', 'Deposited'), ('realized', 'Realized'), ('returned', 'Returned')], default='collected')
    account_fund_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False)
    bank_journal = fields.Many2one('account.journal', "Bank Journal")

    @api.model
    def create(self, vals):
        """Making sure if payment type is cheque the state is cheque_on_hand"""
        if vals.get('payment_type_name') == 'Cheque':
            vals['state'] = 'cheque_on_hand'
        return super(InheritAccountBulkPayment, self).create(vals)

    def deposit_cheque(self):
        """Depositing cheque function"""
        self.write({
            'state': 'deposited'
        })

    def return_check(self):
        """Creating a return cheque and confirming and then opening the created cheque"""
        return_cheque = self.env['returned.checks'].sudo().create({
            'payment_id': self.id,
            'partner_id': self.partner_id.id,
            'amount': self.lines_total_amount,
            'currency_id': self.currency_id.id,
            'state': "draft",
            'company_id': self.company_id.id,
        })

        # confirming the cheque
        return_cheque.sudo().confirm()

        self.write({
            'state': 'returned'
        })

        # opening the created cheque
        return {
            'type': 'ir.actions.act_window',
            'name': _('Return Cheque'),
            'view_mode': 'form',
            'res_model': 'returned.checks',
            'target': 'self',
            'res_id': return_cheque.id,
        }


class AccountJournalInherit(models.Model):
    _inherit = 'account.journal'

    deposit_fund_journal = fields.Boolean(string="Allow Deposited Funds", default=False)

    @api.onchange('type', 'deposit_fund_journal')
    def onchange_type_and_deposit_fund_journal(self):
        """Making sure that if deposit_fund_journal is ticked the journal type is bank"""
        if self.deposit_fund_journal and not self.type == 'bank':
            raise UserError('If deposited funds are allowed, journal type should be bank')


class AccountRegisterPaymentsInherit(models.TransientModel):
    _inherit = 'account.payment.register'

    def create_payments(self):
        """Validating and Making sure if the journal's type is bank and fund transfers allowed"""
        if self.payment_type_name == 'Cheque' and self.invoice_type == 'out_invoice':
            if self.journal_id.type == 'bank' and self.journal_id.deposit_fund_journal:
                pass
            else:
                raise UserError('Please select a Journal with type bank and Allowed Fund Transfer for Cheques.')
        if self.journal_id.deposit_fund_journal and not self.payment_type_name == 'Cheque':
            raise UserError('This Journal can have only Cheque Payments.')
        return super(AccountRegisterPaymentsInherit, self).create_payments()


class DepositedFunds(models.TransientModel):
    _name = 'deposited.funds'

    journal_id = fields.Many2one('account.journal', string="Banking Journal", domain=[('type', '=', 'bank'), ('deposit_fund_journal', '=', False)])

    def deposit_fund(self):
        """Depositing cheque"""
        bulk_payment = self.env['account.bulk.payment'].browse(self.env.context['active_id'])
        journal_entry_items = {
            'name': self.journal_id.sequence_id.next_by_id(),
            'date': datetime.now().date(),
            'journal_id': self.journal_id.id,
            'company_id': bulk_payment.company_id.id,
            'currency_id': bulk_payment.currency_id.id,
            'ref': "Fund Transfer"
        }

        lines = None

        # creating credit entry
        if bulk_payment.partner_type == "customer":
            line_1 = self.post_journal(bulk_payment.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='credit')
        else:
            line_1 = self.post_journal(bulk_payment.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='debit')

        # creating debit entry
        if bulk_payment.partner_type == "customer":
            line_2 = self.post_journal(self.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='debit')
        else:
            line_2 = self.post_journal(self.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='credit')

        journal_entry_items['line_ids'] = [(0, 0, line_1), (0, 0, line_2)]
        journal_entry = self.env['account.move'].create(journal_entry_items)

        # posting journal entry
        journal_entry.post()

        # updating the state
        bulk_payment.write({
            'state': 'realized',
            'account_fund_move_id': journal_entry.id
        })

    def deposit_fund_api(self, bulk_payment):
        """Depositing cheque"""
        bulk_payment = bulk_payment
        journal_entry_items = {
            'name': self.journal_id.sequence_id.next_by_id(),
            'date': datetime.now().date(),
            'journal_id': self.journal_id.id,
            'company_id': bulk_payment.company_id.id,
            'currency_id': bulk_payment.currency_id.id,
            'ref': "Fund Transfer"
        }

        lines = None

        # creating credit entry
        if bulk_payment.partner_type == "customer":
            line_1 = self.post_journal(bulk_payment.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='credit')
        else:
            line_1 = self.post_journal(bulk_payment.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='debit')

        # creating debit entry
        if bulk_payment.partner_type == "customer":
            line_2 = self.post_journal(self.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='debit')
        else:
            line_2 = self.post_journal(self.journal_id.default_credit_account_id.id, bulk_payment.lines_total_amount, amount_type='credit')

        journal_entry_items['line_ids'] = [(0, 0, line_1), (0, 0, line_2)]
        journal_entry = self.env['account.move'].create(journal_entry_items)

        # posting journal entry
        journal_entry.post()

        # updating the state
        bulk_payment.write({
            'state': 'realized',
            'account_fund_move_id': journal_entry.id
        })

    def post_journal(self, account_id, amount, amount_type):
        """Here via this function journal entry lines are created."""
        return {
            'account_id': account_id,
            'credit': amount if amount_type == 'credit' else 0,  # if type is credit then amount is written else 0
            'debit': amount if amount_type == 'debit' else 0,  # if type is debit then amount is written else 0
        }

    def create_bulk_payment(self):
        payment = self.env['account.payment'].browse(self.env.context['active_id'])
        if not payment.bulk_payment_id:
            if payment.partner_type == 'customer':
                if payment.payment_type == 'inbound':
                    sequence_code = 'account.bulk.payment.customer.invoice'
                if payment.payment_type == 'outbound':
                    sequence_code = 'account.bulk.payment.customer.refund'
            if payment.partner_type == 'supplier':
                if payment.payment_type == 'inbound':
                    sequence_code = 'account.bulk.payment.supplier.refund'
                if payment.payment_type == 'outbound':
                    sequence_code = 'account.bulk.payment.supplier.invoice'

            sequence = self.env['ir.sequence'].with_context(ir_sequence_date=payment.payment_date).next_by_code(
                sequence_code)

            BulkPayment = self.env['account.bulk.payment'].create({
                'name': sequence,
                'invoice_type': payment.reconciled_invoice_ids[0].type,
                'currency_id': payment.currency_id.id,
                'payment_date': payment.payment_date,
                'communication': payment.communication,
                'journal_id': payment.journal_id.id,
                'lines_total_amount': payment.amount,
                'lines_total_amount_in_words': payment.check_amount_in_words,
                'partner_type': payment.partner_type,
                'partner_id': payment.partner_id.id,
                'payment_method_id': payment.payment_method_id.id,
                'company_id': payment.journal_id.company_id.id,
                'receipt_no': payment.receipt_no.id,
                'payment_type': payment.payment_type,
                'cheque_no': payment.cheque_no,
                'cheque_date': payment.cheque_date,
                'payment_type_name': payment.payment_type_name,
                'deposited_account_no': payment.deposited_account_no.id,
                'deposited_date': payment.deposited_date,
                'return_cheque': payment.return_cheque,
                'deposited_bank_branch': payment.deposited_bank_branch.id,
                'deposited_bank': payment.deposited_bank.id,
                'account_no': payment.account_no.id,
                'bank': payment.bank.id,
                'bank_journal': self.journal_id.id
            })

            # payment.bulk_payment_id = BulkPayment.id
            BulkPaymentLine = self.env['account.bulk.payment.line']
            for line in payment.reconciled_invoice_ids:
                amount = self.get_payment_of_invoice(json.loads(line.invoice_payments_widget).get('content'), payment)
                BulkPaymentLine.create({
                    'bulk_payment_id': BulkPayment.id,
                    'invoice_id': line.id,
                    'currency_id': line.currency_id.id,
                    'amount': amount
                })

            BulkPayment.deposit_cheque()

            payment.write({
                "bulk_payment_id": BulkPayment.id
            })

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': BulkPayment.id,
                'res_model': 'account.bulk.payment',
                'target': 'current',
            }

    def get_payment_of_invoice(self, content, payment):
        for item in content:
            if item.get('account_payment_id') == payment.id:
                return item.get('amount')


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Account Payable",
                                                  domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  required=True,
                                                  store=True)
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     required=True,
                                                     store=True)