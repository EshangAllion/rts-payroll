from odoo import api, fields, models
import sys
from datetime import datetime, timedelta
import math
from datetime import datetime, timedelta, time


def float_to_time(float_hour):
    """float to time function"""
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)


def convert_to_float(time):
    """convert time to float"""
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)


class AttendanceWizard(models.TransientModel):
    _name = 'attendance.calc.wizard'

    def calculate_attendance(self):
        """Calculating attendances"""
        res_company = self.env['res.company'].sudo().search([])
        for company in res_company:
            hr_employee_list = self.env['hr.employee'].sudo().search([('company_id', '=', company.id)])

            yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
            for employee in hr_employee_list:
                check_in = False
                attendance_log = self.env['attendance.log'].sudo().search([('employee_id', '=', employee.id),
                                                                    ('date', '<=', yesterday), ('is_calculated', '=', False)
                                                                       , ('status', '=', '0')], order='punching_time')
                for log in attendance_log:
                    if not check_in == log.date:
                        self.env['hr.attendance'].sudo().create({
                            'employee_id': log.employee_id.id,
                            'check_in': log.punching_time,
                            'date': log.date
                        })
                        check_in = log.date
                    log.is_calculated = True

            for employee in hr_employee_list:
                check_out = False
                attendance_log = self.env['attendance.log'].sudo().search([('employee_id', '=', employee.id),
                                                                    ('date', '<=', yesterday), ('is_calculated', '=', False)
                                                                       , ('status', '=', '1')], order="punching_time desc")
                for log in attendance_log:
                    if not check_out == log.date:
                        hr_attendence_check = self.env['hr.attendance'].sudo().search([('date', '=', log.date),
                                                                                ('employee_id', '=', log.employee_id.id)])
                        if hr_attendence_check:
                            if hr_attendence_check.check_in > log.punching_time:
                                pass
                            else:
                                if hr_attendence_check:
                                    hr_attendence_check.write({
                                        'check_out': log.punching_time
                                    })
                                check_out = log.date
                    log.is_calculated = True
