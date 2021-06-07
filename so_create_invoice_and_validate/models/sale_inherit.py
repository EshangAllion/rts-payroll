from odoo import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """in this function, create invoice from sale order. reduce 'create invoice by invoice line' step"""

        res = super(SaleOrder, self).action_confirm()  # get super class to the object
        # is_so_bypass = self.env["res.company"].search()

        if self.company_id.so_step_bypass == True:  # check company id has invoice Auto Create option
            if res:
                self._create_invoices()   # Creates invoice(s) for repair order
                for invoice in self.invoice_ids:  # search for relevant invoices and validate
                    invoice.action_post()  # get the relevant invoice and validate
        return res