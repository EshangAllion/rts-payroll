from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug import url_encode


class ReturnChecksPaymentWizards(models.TransientModel):
    _name = "return.checks.payment.wizards"

    @api.model
    def _default_partner_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        return_checks = self.env['returned.checks'].browse(active_ids)
        return return_checks.partner_id.id

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, default=_default_partner_id)
    partner_bank_account_id = fields.Many2one('res.partner.bank', string="Recipient Bank Account")
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo')
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method')
    show_partner_bank_account = fields.Boolean(compute='_compute_show_partner_bank')

    manual_check_number = fields.Char(string="Check Number")
    cheque_no = fields.Char(string="Cheque/Slip No.")
    cheque_date = fields.Date(string='Cheque/Slip Date', default=fields.Date.context_today)
    payment_type_name = fields.Char(related='payment_method_id.name')
    deposited_account_no = fields.Many2one('res.partner.bank', string="Deposited Bank Account")
    deposited_date = fields.Date(string='Deposited Date', default=fields.Date.context_today)
    return_cheque = fields.Boolean(string="Return Cheque")
    deposited_bank_branch = fields.Many2one('res.country.state', string="Deposited Bank Branch")
    deposited_bank = fields.Many2one('res.bank', string="Deposited Bank")
    account_no = fields.Many2one('res.partner.bank', string="Bank Account", related='journal_id.bank_account_id')
    bank = fields.Many2one('res.bank', string="Bank")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Onchange partner ID, the bank account of partner is assigned to partner_bank_account_id"""
        if self.partner_id and len(self.partner_id.bank_ids) > 0:
            self.partner_bank_account_id = self.partner_id.bank_ids[0]
        else:
            self.partner_bank_account_id = False

    @api.constrains('amount')
    def _check_amount(self):
        """Validation to avoid amount greater than 0"""
        if not self.amount > 0.0:
            raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.depends('payment_method_id')
    def _compute_show_partner_bank(self):
        """ Computes if the destination bank account must be displayed in the payment form view. By default, it
        won't be displayed but some modules might change that, depending on the payment type."""
        for payment in self:
            payment.show_partner_bank_account = payment.payment_method_id.code in self.env['account.payment']._get_method_codes_using_bank_account()

    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        """Hide payment method if there is no journal selected fot the payment"""
        if not self.journal_id:
            self.hide_payment_method = True
            return
        journal_payment_methods = self.journal_id.inbound_payment_method_ids
        self.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.journal_id.inbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            return {'domain': {'payment_method_id': [('id', 'in', payment_methods.ids)]}}
        return {}

    def _get_payment_vals(self, return_checks):
        """ Hook for extension, getting all necessary data to create a payment"""
        return {
            'partner_type': return_checks.payment_id.partner_type,
            'payment_type': return_checks.payment_id.payment_type,
            'partner_id': self.partner_id.id,
            'partner_bank_account_id': self.partner_bank_account_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,

            'cheque_no': self.cheque_no,
            'manual_check_number': self.manual_check_number,
            'cheque_date': self.cheque_date,
            'payment_type_name': self.payment_type_name,
            'deposited_account_no': self.deposited_account_no.id,
            'deposited_date': self.deposited_date,
            'return_cheque': self.return_cheque,
            'deposited_bank_branch': self.deposited_bank_branch.id,
            'deposited_bank': self.deposited_bank.id,
            'account_no': self.account_no.id,
            'bank': self.bank.id,
        }

    def post_payment(self):
        """Posting the payment, by reconciling and hitting it to journals via journal entry"""
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        return_checks = self.env['returned.checks'].browse(active_ids)

        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals(return_checks))
        payment.post()

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + return_checks.account_move_id.line_ids:
            if line.account_id.internal_type == 'receivable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()

        # creating bulk payment
        bulk_payment = self.env['account.bulk.payment'].create({
            "name": "Returned Check Payment for " + str(return_checks.name),
            'partner_type': return_checks.payment_id.partner_type,
            'payment_type': return_checks.payment_id.payment_type,
            'partner_id': self.partner_id.id,
            'payment_method_id': self.payment_method_id.id,
            'lines_total_amount': self.amount,
            'payment_date': self.payment_date,
            'cheque_no': self.cheque_no,
            'communication': self.communication,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'invoice_type': 'out_invoice',
            'manual_check_number': self.manual_check_number,
            'cheque_date': self.cheque_date,
            'payment_type_name': self.payment_type_name,
            'deposited_account_no': self.deposited_account_no.id,
            'deposited_date': self.deposited_date,
            'return_cheque': self.return_cheque,
            'deposited_bank_branch': self.deposited_bank_branch.id,
            'deposited_bank': self.deposited_bank.id,
            'account_no': self.account_no.id,
            'bank': self.bank.id,
        })

        for return_check in return_checks:
            return_check.set_to_paid(self.amount, return_check.paid_amount, bulk_payment.id)

        # hitting payment id to bulk payment
        payment.write({
            'bulk_payment_id': bulk_payment.id
        })

        # Log the payment in the chatter
        body = (_(
            "A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your returned check %s has been made.") % (
                payment.amount, payment.currency_id.symbol,
                url_encode({'model': 'account.bulk.payment', 'res_id': bulk_payment.id}), bulk_payment.name, bulk_payment.name))
        return_checks.message_post(body=body)

        return {'type': 'ir.actions.act_window_close'}
