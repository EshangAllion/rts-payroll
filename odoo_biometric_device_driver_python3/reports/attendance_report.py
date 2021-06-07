from odoo import models, api, fields
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import base64, os
from odoo.tools import misc
import xlsxwriter


class AttendanceReport(models.TransientModel):
    _name = 'attendance.report'

    date_from = fields.Date('From', required=True, default=datetime.today())
    date_to = fields.Date('To', required=True, default=datetime.today())
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)
    type = fields.Selection([('employee', 'Employee'), ('department', 'Department')], string='Type', default='employee')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_id = fields.Many2one('hr.department', string='Department')

    def export_attendance_xlsx(self):
        """generating xlsx report according to th values"""
        self.env['attendance.calc.wizard'].calculate_attendance()
        if self.type == 'employee':
            if not self.employee_ids:
                raise UserError("Please Select At Least One Employee.")
            report_data = self.get_report_data(self.date_from, self.date_to, self.employee_ids)
        elif self.type == 'department':
            if not self.department_id:
                raise UserError("Please Select a Department.")
            employees = self.env['hr.employee'].search([('department_id', '=', self.department_id.id)])
            report_data = self.get_report_data(self.date_from, self.date_to, employees)
        else:
            raise UserError("Please Select Either Employee or Department")

        # opening xlsx report

        report = open(report_data, 'rb+').read()
        output = base64.encodestring(report)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': report})
        self.env.args = cr, uid, misc.frozendict(context)
        self.report_name = report_data
        self.report_file = ctx['report_file']
        self.is_printed = True

        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.report',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(report_data)
        return result

    def daterange(self, start_date, end_date):
        """Function returns date range"""
        for date in range(int(((end_date + timedelta(days=1)) - start_date).days)):
            yield start_date + timedelta(date)

    def get_report_data(self, date_from, date_to, employee_ids):
        """Generating report content, actually creating the headings and data for the report"""
        report_data = os.path.join(os.path.dirname(__file__), 'Attendance from ' + self.date_from + " to " + self.date_to + '.xlsx')
        workbook = xlsxwriter.Workbook(report_data)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
        date_from = datetime.strptime(date_from, "%Y-%m-%d").date()

        # layout designs, fonts
        font_center = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 10, 'font_name': 'Arial'})
        font_center_red = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 10, 'font_name': 'Arial', 'font_color': 'red'})
        font_center_orange = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 10, 'font_name': 'Arial', 'font_color': 'orange'})
        font_bold_center = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 12, 'bold': True, 'font_name': 'Arial'})
        font_bold_center_wrap = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 12, 'bold': True, 'text_wrap': True, 'font_name': 'Arial'})

        row = 0
        column = 0

        worksheet.set_row(4, 20)
        worksheet.set_row(5, 20)
        worksheet.freeze_panes(6, 7)

        worksheet.merge_range(row, column, row + 3, column + 6, "", font_bold_center)
        column += 7

        for date in self.daterange(date_from, date_to):
            worksheet.merge_range(row, column, row + 3, column + 5, str(date.strftime("%Y-%m-%d") + " , " + str(date.strftime("%A")))  + " " + self.get_resource_leave(date), font_bold_center)
            column += 6

        row += 4
        column_sub = 0

        # generating heading
        worksheet.merge_range(row, column_sub, row + 1, column_sub + 2, "Employee Name", font_bold_center)
        column_sub += 3
        worksheet.merge_range(row, column_sub, row + 1, column_sub + 1, "Attendance No.", font_bold_center_wrap)
        column_sub += 2
        worksheet.merge_range(row, column_sub, row + 1, column_sub + 1, "Team", font_bold_center)
        column_sub += 2
        for column_number in range(0, column - column_sub, 6):
            column_total = column_sub + column_number
            worksheet.merge_range(row, column_total, row + 1, column_total, "In", font_bold_center)
            worksheet.merge_range(row, column_total + 1, row + 1, column_total + 1, "Out", font_bold_center)
            worksheet.merge_range(row, column_total + 2, row + 1, column_total + 2, "Total Hours Worked", font_bold_center_wrap)
            worksheet.merge_range(row, column_total + 3, row + 1, column_total + 3, "PR/AB", font_bold_center)
            worksheet.merge_range(row, column_total + 4, row + 1, column_total + 5, "Leave Status", font_bold_center)

        row += 2
        column_data = 0
        # generating data
        for employee in employee_ids:
            worksheet.merge_range(row, column_data, row, column_data + 2, employee.name, font_center)
            column_data += 3
            worksheet.merge_range(row, column_data, row, column_data + 1, employee.employee_number, font_center)
            column_data += 2
            worksheet.merge_range(row, column_data, row, column_data + 1, employee.department_id.name, font_center)
            column_data += 2
            for date in self.daterange(date_from, date_to):
                for column_number in range(0, column - column_data, 6):
                    attendance = self.get_attendance(date, employee)
                    total_column = column_data + column_number
                    worksheet.write(row, total_column, attendance.get('in_time'), font_center_red if attendance.get('in_time_float') > 9 else font_center)
                    worksheet.write(row, total_column + 1, attendance.get('out_time'), font_center)
                    worksheet.write(row, total_column + 2, attendance.get('worked_hours'), font_center_orange if attendance.get('worked_hours_float') > 4 and int(attendance.get('worked_hours_float')) < 7 else font_center)
                    worksheet.write(row, total_column + 3, attendance.get('state'), font_center)
                    worksheet.merge_range(row, total_column + 4, row, total_column + 5, attendance.get('leave_state'), font_center)
                    column_data += 6
                    break
            row += 1
            column_data = 0

        workbook.close()
        return report_data

    def get_attendance(self, date, employee):
        """Get data of attendance according to employee and date"""
        attendance = self.env['hr.attendance'].search([('date', '=', str(date)), ('employee_id', '=', employee.id)], limit=1)
        if attendance:
            res = {
                'in_time': '{0:02.0f}:{1:02.0f}'.format(*divmod(attendance.in_time * 60, 60)),
                'out_time': '{0:02.0f}:{1:02.0f}'.format(*divmod(attendance.out_time * 60, 60)),
                'worked_hours': '{0:02.0f}:{1:02.0f}'.format(*divmod(attendance.worked_hours * 60, 60)),
                'in_time_float':  attendance.in_time,
                'worked_hours_float':  attendance.worked_hours,
                'state': 'PR',
                'leave_state': self.get_holiday(date, employee).get('reason')
            }
        else:
            res = {
                'in_time': '',
                'out_time': '',
                'worked_hours': '0.0',
                'in_time_float': 0.0,
                'worked_hours_float':  0.0,
                'state': 'AB',
                'leave_state': self.get_holiday(date, employee).get('reason')
            }
        return res

    def get_holiday(self, date, employee):
        """Get holidays of the employee according to date"""
        attendance = self.env['hr.holidays'].search([('date_from_only_date', '<=', str(date)), ('date_to_only_date', '>=', str(date)), ('employee_id', '=', employee.id), ('type', '=', 'remove')], limit=1)
        if attendance:
            res = {
                'reason': 'Applied/' + (attendance.state).capitalize(),
            }
        else:
            res = {
                'reason': 'Not Applied/Not Informed',
            }
        return res

    def action_back(self):
        """Back button faction to go back"""
        if self._context is None:
            self._context = {}
        self.is_printed = False
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'attendance.report',
            'target': 'new',
        }
        return result

    def get_resource_leave(self, date):
        """Getting global leaves"""
        leaves = self.env['resource.calendar.leaves'].search([('date_from_temp', '<=', str(date)), ('date_to_temp', '>=', str(date)), ('resource_id', '=', False)], limit=1)
        if leaves:
            return leaves.name
        else:
            return ""


