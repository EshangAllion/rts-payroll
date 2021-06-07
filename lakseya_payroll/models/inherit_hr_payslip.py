from datetime import datetime, timedelta
from odoo import api, fields, models, tools, _


class InheritHrPayslip(models.Model):

    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        """Overiding onchange function in core"""
        return_obj = super(InheritHrPayslip, self)._onchange_employee()
        if self.employee_id and self.date_from and self.date_to:
            inputs = []
            self.input_line_ids = None
            inputs.append((0, 0, self.get_commissions()))
            inputs.append((0, 0, self.get_normal_ot()))
            inputs.append((0, 0, self.get_double_ot()))
            inputs.append((0, 0, self.get_nopay()))
            self.input_line_ids = inputs
        return return_obj

    def get_commissions(self):
        """Calculating commissions of each employee, triggered by onchange function"""
        commission_slab = self.env['commission.slab.configuration'].search(
            [('employee_ids', 'in', self.employee_id.id)])
        overall_commissions = 0
        for slab in commission_slab:
            commission_total = 0
            sale_order_lines = self.env['account.move.line'].search(
                [('employee_id', '=', self.employee_id.id), ('move_id.invoice_date', '>=', self.date_from),
                 ('product_id.type', '=', 'service'), ('move_id.invoice_payment_state', '=', 'paid'),
                 ('move_id.invoice_date', '<=', self.date_to), ('department_id', '=', slab.department_id.id)])
            if sale_order_lines:
                for line in sale_order_lines:
                    commission_total += line.price_subtotal
                commission_line = slab.slab_config_ids.filtered(
                    lambda x: x.revenue_start_amount <= commission_total and x.revenue_end_amount >= commission_total)
                if commission_line.line_id.commission_type == 'percentage':
                    overall_commissions += commission_total * (commission_line.amount / 100)
                else:
                    overall_commissions += commission_line.amount
        return {
            "input_type_id": self.env.ref('lakseya_payroll.input_commission').id,
            "amount": overall_commissions
        }

    def get_normal_ot(self):
        """Calculating Normal OT of each employee, triggered by onchange function"""
        ot = 0
        for attendance in self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id), ('date', '>=', str(self.date_from)), ('date', '<=', str(self.date_to)), ('ot_hours', '>', 0)]):
            ot += attendance.ot_hours
        return {
            "input_type_id": self.env.ref('lakseya_payroll.input_normal_ot').id,
            "amount": ot
        }

    def get_double_ot(self):
        """Calculating Double OT of each employee, triggered by onchange function"""
        ot = 0
        for attendance in self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id), ('date', '>=', str(self.date_from)), ('date', '<=', str(self.date_to)), ('ot_double_hours', '>', 0)]):
            ot += attendance.ot_double_hours
        return {
            "input_type_id": self.env.ref('lakseya_payroll.input_double_ot').id,
            "amount": ot
        }

    def get_nopay(self):
        """Calculating Nopay of each employee, triggered by onchange function"""
        nopay = 0
        start_date = self.date_from
        end_date = self.date_to
        delta = timedelta(days=1)
        while start_date <= end_date:
            if self._check_attendance(start_date, self.employee_id.id) or self._check_holiday(start_date) or self._check_leave(start_date, self.employee_id.id):
                pass
            else:
                nopay += 1
            start_date += delta
        return {
            "input_type_id": self.env.ref('lakseya_payroll.input_nopay').id,
            "amount": nopay
        }

    def _check_holiday(self, date):
        """Getting Holidays, triggered by onchange function"""
        global_leave = self.env['resource.holidays'].search([('start_date', '>=', str(date)), ('end_date', '<=', str(date))])
        if global_leave:
            return True
        else:
            return False

    def _check_leave(self, date, employee_id):
        """Check Leaves of employees"""
        hr_leave = self.env['hr.leave'].search([('request_date_from', '>=', str(date)), ('request_date_to', '<=', str(date)), ('employee_id', '=', employee_id), ('state', 'in', ['confirm', 'validate1', 'validate'])])
        if hr_leave:
            return True
        else:
            return False

    def _check_attendance(self, date, employee_id):
        """Check attendances of employees"""
        attendance = self.env['hr.attendance'].search([('date', '=', str(date)), ('employee_id', '=', employee_id)])
        if attendance:
            return True
        else:
            return False


