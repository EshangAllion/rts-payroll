from odoo import fields, models, api


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    def _default_employee(self):
        """Return default Employee"""
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, index=True)




class InheritSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department',  string='Department')

    def _prepare_invoice_line(self,):
        """Preparing invoice line"""
        invoice_vals = super(InheritSaleOrderLine, self)._prepare_invoice_line()
        invoice_vals.update({
            'employee_id': self.employee_id,
            'department_id': self.department_id,
        })
        return invoice_vals


class InheritAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    def _default_employee(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee, index=True)
    album = fields.Char('Album')

    def _prepare_invoice(self, ):
        """inheriting function that sends data to invoice"""
        invoice_vals = super(InheritSaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'employee_id': self.employee_id.id,
        })
        return invoice_vals
