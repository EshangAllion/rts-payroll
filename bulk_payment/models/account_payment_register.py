from odoo import fields, api, models, _
from collections import defaultdict
from odoo.exceptions import UserError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}


class InheritPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    payment_lines = fields.One2many(string='Payment Lines', comodel_name='account.register.payment.line',
                                    inverse_name='acc_reg_payment_id')
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], readonly=True, copy=False)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')
    name = fields.Char(readonly=True, copy=False, default="New Bulk Payment")
    communication = fields.Char(string="Communication")
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('out_receipt', 'Customer Receipt'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('in_receipt', 'Vendor Receipt'),
    ])
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    lines_total_amount = fields.Monetary(string='Payment Amount', compute='update_lines_total_amount')
    lines_total_amount_in_words = fields.Char(string="Amount in Words")

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

    @api.onchange('lines_total_amount')
    def update_lines_total_amount_in_words(self):
        """
        compute lines total amount in words
        """
        self.lines_total_amount_in_words = self.currency_id.amount_to_text(self.lines_total_amount)

    @api.model
    def default_get(self, fields):
        """
        if user select invoices before bulk payment,
        need to load relevant invoices and their amounts with the form view
        """
        rec = super(InheritPaymentRegister, self).default_get(fields)
        active_ids = self._context.get('active_ids')

        if active_ids:
            # load payment lines to the form view
            invoices = self.env['account.move'].browse(active_ids)
            if any(inv.partner_id != invoices[0].partner_id for inv in invoices):
                raise UserError(_("You can only register at the same time for payment that are all from the same partner"))
            if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
                raise UserError(_("You can only register at the same time for payment that are all from the same currency"))
            payment_lines = self._default_payment_lines(invoices)
            invoice_type = invoices[0].type
            rec.update({
                'payment_lines': payment_lines,
                'invoice_type': invoice_type,
            })
        return rec

    def _default_payment_lines(self, invoices):
        """
        need to return payment lines by adding given invoice data
        """
        new_payment_lines = []
        for invoice in invoices:
            amount = self._compute_payment_amount(invoice, invoice.currency_id, self.journal_id, self.payment_date)
            new_payment_lines.append((0, 0, {
                'invoice_id': invoice.id,
                'amount': abs(amount),
                'invoice_total': invoice.amount_total,
                'currency_id': invoice.currency_id.id,
                'invoice_due': invoice.amount_residual
            }))
        return new_payment_lines

    @api.depends('payment_lines', 'payment_lines.amount')
    def update_lines_total_amount(self):
        """
        update total line amounts
        """
        for payment in self:
            payment.lines_total_amount = sum([line.amount for line in payment.payment_lines if line.amount])

    @api.onchange('journal_id')
    def update_payment_lines_amounts(self):
        """
        if user change journal, need to compute line amounts according to journal currency
        """
        for line in self.payment_lines:
            line.amount = abs(self._compute_payment_amount(line.invoice_id, line.invoice_id.currency_id, self.journal_id, self.payment_date))

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.

        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
                SELECT
                    move.type AS type,
                    move.currency_id AS currency_id,
                    SUM(line.amount_residual) AS amount_residual,
                    SUM(line.amount_residual_currency) AS residual_currency
                FROM account_move move
                LEFT JOIN account_move_line line ON line.move_id = move.id
                LEFT JOIN account_account account ON account.id = line.account_id
                LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
                WHERE move.id IN %s
                AND account_type.type IN ('receivable', 'payable')
                GROUP BY move.id, move.type
            ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        for res in query_res:
            move_currency = self.env['res.currency'].browse(res['currency_id'])
            if move_currency == currency and move_currency != company.currency_id:
                total += res['residual_currency']
            else:
                total += company.currency_id._convert(res['amount_residual'], currency, company, date)
        return total

    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices/bills to pay. In case of multiple
            documents, they need to be grouped by partner, bank, journal and
            currency.
        :return: The payment values as a dictionary.
        '''
        values = {
            'journal_id': self.journal_id.id,
            'receipt_no': self.receipt_no.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in invoices.invoice_id),
            'invoice_ids': [(6, 0, invoices.invoice_id.ids)],
            'payment_type': invoices.acc_reg_payment_id.payment_type,
            'amount': abs(invoices.amount),
            'currency_id': invoices.invoice_id.currency_id.id,
            'partner_id': invoices.invoice_id.commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices.invoice_id.type],
            'partner_bank_account_id': invoices.invoice_id.invoice_partner_bank_id.id,
            'company_id': self.journal_id.company_id.id,
            'cheque_no': self.cheque_no,
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
        return values

    def get_payments_vals(self):
        '''Compute the values for payments.

        :return: a list of payment values (dictionary).
        '''
        grouped = defaultdict(lambda: self.env["account.register.payment.line"])
        for inv in self.payment_lines:
            if self.group_payment:
                grouped[(inv.invoice_id.commercial_partner_id, inv.invoice_id.currency_id, inv.invoice_id.invoice_partner_bank_id, MAP_INVOICE_TYPE_PARTNER_TYPE[inv.invoice_id.type])] += inv.id
            else:
                grouped[inv.id] += inv
        return [self._prepare_payment_vals(invoices) for invoices in grouped.values()]

    def create_payments(self):
        '''Create payments according to the invoices.
        Having invoices with different commercial_partner_id or different type
        (Vendor bills with customer invoices) leads to multiple payments.
        In case of all the invoices are related to the same
        commercial_partner_id and have the same type, only one payment will be
        created.

        :return: The ir.actions.act_window to show created payments.
        '''
        # get relevant sequence
        if not self.payment_type:
            self.payment_type = 'inbound' if self.payment_lines[0].invoice_id.type in ['in_refund', 'out_invoice'] else 'outbound'
        if not self.partner_type:
            self.partner_type = MAP_INVOICE_TYPE_PARTNER_TYPE[self.payment_lines[0].invoice_id.type]
        if self.partner_type == 'customer':
            if self.payment_type == 'inbound':
                sequence_code = 'account.bulk.payment.customer.invoice'
            if self.payment_type == 'outbound':
                sequence_code = 'account.bulk.payment.customer.refund'
        if self.partner_type == 'supplier':
            if self.payment_type == 'inbound':
                sequence_code = 'account.bulk.payment.supplier.refund'
            if self.payment_type == 'outbound':
                sequence_code = 'account.bulk.payment.supplier.invoice'

        self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.payment_date).next_by_code(sequence_code)

        BulkPayment = self.env['account.bulk.payment'].create({
            'name': self.name,
            'invoice_type': self.invoice_type,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'journal_id': self.journal_id.id,
            'lines_total_amount': self.lines_total_amount,
            'lines_total_amount_in_words': self.lines_total_amount_in_words,
            'partner_type': self.partner_type,
            'partner_id': self.payment_lines[0].invoice_id.partner_id.id,
            'payment_method_id': self.payment_method_id.id,
            'company_id': self.journal_id.company_id.id,
            'receipt_no': self.receipt_no.id,
            'payment_type': self.payment_type,
            'cheque_no': self.cheque_no,
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

        Payment = self.env['account.payment']
        BulkPaymentLine = self.env['account.bulk.payment.line']
        payments = Payment.create(self.get_payments_vals())
        payments.post()
        for payment in payments:
            payment.bulk_payment_id = BulkPayment.id
            BulkPaymentLine.create({
                'bulk_payment_id': BulkPayment.id,
                'invoice_id': payment.invoice_ids[0].id,
                'currency_id': payment.invoice_ids[0].currency_id.id,
                'amount': payment.amount
            })

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': BulkPayment.id,
            'res_model': 'account.bulk.payment',
            'target': 'current',
        }

    def create_payments_api(self):
        '''Create payments according to the invoices.
        Having invoices with different commercial_partner_id or different type
        (Vendor bills with customer invoices) leads to multiple payments.
        In case of all the invoices are related to the same
        commercial_partner_id and have the same type, only one payment will be
        created.

        :return: The ir.actions.act_window to show created payments.
        '''
        # get relevant sequence
        if not self.payment_type:
            self.payment_type = 'inbound' if self.payment_lines[0].invoice_id.type in ['in_refund', 'out_invoice'] else 'outbound'
        if not self.partner_type:
            self.partner_type = MAP_INVOICE_TYPE_PARTNER_TYPE[self.payment_lines[0].invoice_id.type]
        if self.partner_type == 'customer':
            if self.payment_type == 'inbound':
                sequence_code = 'account.bulk.payment.customer.invoice'
            if self.payment_type == 'outbound':
                sequence_code = 'account.bulk.payment.customer.refund'
        if self.partner_type == 'supplier':
            if self.payment_type == 'inbound':
                sequence_code = 'account.bulk.payment.supplier.refund'
            if self.payment_type == 'outbound':
                sequence_code = 'account.bulk.payment.supplier.invoice'

        self.name = self.env['ir.sequence'].with_context(ir_sequence_date=self.payment_date).next_by_code(sequence_code)

        BulkPayment = self.env['account.bulk.payment'].sudo().create({
            'name': self.name,
            'invoice_type': self.invoice_type,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'journal_id': self.journal_id.id,
            'lines_total_amount': self.lines_total_amount,
            'lines_total_amount_in_words': self.lines_total_amount_in_words,
            'partner_type': self.partner_type,
            'partner_id': self.payment_lines[0].invoice_id.partner_id.id,
            'payment_method_id': self.payment_method_id.id,
            'company_id': self.journal_id.company_id.id,
            'receipt_no': self.receipt_no.id,
            'payment_type': self.payment_type,
            'cheque_no': self.cheque_no,
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

        Payment = self.env['account.payment']
        BulkPaymentLine = self.env['account.bulk.payment.line']
        payments = Payment.create(self.get_payments_vals())
        payments.post()
        for payment in payments:
            payment.bulk_payment_id = BulkPayment.id
            BulkPaymentLine.create({
                'bulk_payment_id': BulkPayment.id,
                'invoice_id': payment.invoice_ids[0].id,
                'currency_id': payment.invoice_ids[0].currency_id.id,
                'amount': payment.amount
            })

        return BulkPayment

class AccountRegisterPaymentLine(models.TransientModel):
    _name = "account.register.payment.line"

    acc_reg_payment_id = fields.Many2one(string='Account Register Payment', comodel_name='account.payment.register')
    invoice_id = fields.Many2one(string='Invoice/Vendor Bill', comodel_name='account.move', required=True)
    currency_id = fields.Many2one('res.currency')
    amount = fields.Monetary(string='Payment Amount', required=True)
    invoice_total = fields.Monetary(string="Invoice Total")
    invoice_due = fields.Monetary(string="Invoice Due")
