from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.tools import float_compare


class ReturnedChecks(models.Model):
    _name = 'returned.checks'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Returned Checks"

    name = fields.Char(string="Name", track_visibility='onchange')
    payment_id = fields.Many2one('account.bulk.payment', string="Cheque Payment", required=True, domain=[('payment_method_id.name', '=', 'Cheque'), ('is_returned', '=', False), ('payment_type', '=', 'inbound')], track_visibility='onchange')
    bulk_payment_id = fields.Many2one('account.bulk.payment', string="Bulk Payment")
    bulk_payment_ids = fields.Many2many('account.bulk.payment', string="Bulk Payment")
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, related='payment_id.partner_id', track_visibility='onchange')
    amount = fields.Monetary(string="Payment Amount", required=True, related='payment_id.lines_total_amount', track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, copy=False, related='payment_id.currency_id', track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'), ('paid', 'Paid')], string="States", default="draft", copy=False, track_visibility='onchange')
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False, track_visibility='onchange')
    paid_amount = fields.Float(string="Paid Amount", track_visibility='onchange')
    company_id = fields.Many2one('res.company', related='payment_id.company_id')
    payment_type_name = fields.Char(related='payment_id.name')
    overdue_amount = fields.Monetary(compute='_compute_overdue_amount', string='Outstanding Amount', search='_set_overdue_amount')
    date = fields.Date('Date', default=fields.Date.context_today)

    @api.model
    def create(self, vals):
        """this function will create return cheque sequences"""
        if self.env['account.bulk.payment'].browse(vals.get('payment_id')).is_returned == False:
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence.returned.checks')  # create sequence
            return_obj = super(ReturnedChecks, self).create(vals)
            return_obj.payment_id.write({
                'is_returned': True
            })
            return return_obj  # return super class
        else:
            raise UserError("This payment has been returned once")

    def unlink(self):
        """this function will give ability to delete return cheque.
        but cannot delete open and paid return cheque"""
        for return_check in self:
            if return_check.state in ['open', 'paid']:  # check the return cheque state open or paid
                raise UserError(_('You cannot delete a posted or return cheque.'))
        super(ReturnedChecks, self).unlink()  # return super class

    def confirm(self):
        """Creating Journal Entry for the return check"""
        journal_entry_items = {
            'name': self.payment_id.journal_id.sequence_id.next_by_id(),
            'date': datetime.now().date(),
            'journal_id': self.payment_id.journal_id.id,
            # 'company_id': self.payment_id.company_id.id,
            'currency_id': self.payment_id.currency_id.id,
            'ref': "Customer Return Check"
        }

        lines = None
        # creating credit entry
        if self.payment_id.partner_type == "customer":
            line_1 = self.post_journal(self.payment_id.journal_id.default_credit_account_id.id, self.name, self.amount, self.partner_id.id, amount_type='credit')
        else:
            line_1 = self.post_journal(self.payment_id.journal_id.default_credit_account_id.id, self.name, self.amount, self.partner_id.id, amount_type='debit')
        # creating debit entry
        if self.payment_id.partner_type == "customer":
            line_2 = self.post_journal(self.partner_id.with_context(force_company=self.company_id.id).property_account_receivable_id.id, self.payment_id.name, self.amount, self.partner_id.id, amount_type='debit')
        else:
            line_2 = self.post_journal(self.partner_id.with_context(force_company=self.company_id.id).property_account_payable_id.id, self.payment_id.name, self.amount, self.partner_id.id, amount_type='credit')


        journal_entry_items['line_ids'] = [(0, 0, line_1), (0, 0, line_2)]
        journal_entry = self.env['account.move'].create(journal_entry_items)
        # posting journal entry
        journal_entry.post()

        # updating the state
        self.write({
            'state': 'open',
            'account_move_id': journal_entry.id
        })

        self.payment_id.write({
            'account_fund_move_id': journal_entry.id
        })

    def post_journal(self, account_id, name, amount, partner_id, amount_type):
        """Here via this function journal entry lines are created."""
        return {
            'account_id': account_id,
            'name': name,
            'partner_id': partner_id,
            'credit': amount if amount_type == 'credit' else 0,  # if type is credit then amount is written else 0
            'debit': amount if amount_type == 'debit' else 0,  # if type is debit then amount is written else 0
        }

    def set_to_paid(self, paid_amount, returned_check_paid_amount, bulk_payment_id):
        """this function will check payment of the debtor and
        if debtor don't have due state will change open ro paid'"""
        self.write({'paid_amount': (returned_check_paid_amount + paid_amount), 'bulk_payment_ids': [(4, bulk_payment_id)]})
        if self.paid_amount >= self.amount:  # check residual value and total amount
            self.write({'state': 'paid', 'bulk_payment_ids': [(4, bulk_payment_id)]})  # change state

    def _compute_overdue_amount(self):
        """Calculating Real outstanding by excluding all draft cheque payments"""
        for line in self:
            overdue_amount = line.amount - line.paid_amount
            if line.bulk_payment_ids:
                for payment in line.bulk_payment_ids:
                    if payment.state in ['cheque_on_hand', 'deposited']:
                        overdue_amount += payment.lines_total_amount
            line.overdue_amount = overdue_amount

    def _set_overdue_amount(self, operator, value):
        """search function for overdue_amount"""
        all_invoice = self.search([])
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


