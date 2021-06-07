from odoo import models, api, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id_check_return_checks(self):
        """Checking whether the customer have any returned cheques, if contains a warning message will be popped up."""
        if self.partner_id:
            returned_checks = self.env['returned.checks'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'open')])
            count = 0
            total_outstanding = 0
            if returned_checks:
                for check in returned_checks:
                    count += 1
                    total_outstanding += check.amount - check.paid_amount
                message = _('This customer have %s returned cheques with an outstanding of %s') % \
                          (count, total_outstanding)
                warning_mess = {
                    'title': _('Warning'),
                    'message': message
                }
                return {'warning': warning_mess}


class InheritResPartner(models.Model):

    _inherit = 'res.partner'

    return_checks_count = fields.Float(compute='_compute_returned_checks_count', string='Sold')

    def _compute_returned_checks_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        for line in self:
            line.return_checks_count = self.env['returned.checks'].search_count(
                [('partner_id', '=', line.id), ('state', '=', 'open')])

    def open_returned_checks(self):
        """Show returned Checks of the relevant customer"""
        returned_checks = self.env['returned.checks'].search([('partner_id', '=', self.id), ('state', '=', 'open')])
        action = self.env.ref('returned_checks.act_view_return_checks').read()[0]
        action['domain'] = [('id', 'in', returned_checks.ids)]
        return action
