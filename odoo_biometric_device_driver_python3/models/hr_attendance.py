from odoo import models, fields, api, exceptions, _
import math
from datetime import datetime, time, timedelta
from time import mktime


def float_to_time(float_hour):
    return time(int(math.modf(float_hour)[1]), int(60 * math.modf(float_hour)[0]), 0)


def convert_to_float(time):
    hour = int(time[10:13])
    mins = float(time[14:16])
    float_min = mins / 60
    return hour + float_min - math.floor(float_min)


def convert_date_to_float(date_obj):
    obj = datetime.datetime.strptime(str(date_obj), '%H:%M:%S')
    float_value = float(0.00)

    float_value += float(obj.hour) * 3600
    float_value += float(obj.minute) * 60
    float_value += float(obj.second)
    return float(float_value)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    date = fields.Date('Date')
    in_time = fields.Float('In Time', compute='_get_in_time', readonly=True)
    out_time = fields.Float('Out Time', compute='_get_out_time', readonly=True)
    ot_hours = fields.Float('Normal OT Time', compute='_get_normal_ot_time', readonly=True)
    ot_double_hours = fields.Float('Double OT Time', compute='_get_double_ot_time', readonly=True)

    def _get_normal_ot_time(self):
        """get normal ot of employee"""
        for line in self:
            if line.employee_id and line.date:
                if self._check_leave(line.date, line.employee_id.id) or self._check_holiday(line.date):
                    line.ot_hours = 0
                elif line.worked_hours > line.employee_id.resource_calendar_id.hours_per_day and line.date.isoweekday() in [1, 2, 3, 4, 5, 7]:
                    line.ot_hours = line.worked_hours - line.employee_id.resource_calendar_id.hours_per_day
                elif line.worked_hours > 5 and line.date.isoweekday() in [6]:
                    line.ot_hours = line.worked_hours - 5
                else:
                    line.ot_hours = 0
            else:
                line.ot_hours = 0

    def _get_double_ot_time(self):
        """get double ot of employee"""
        for line in self:
            if line.employee_id and line.date:
                if self._check_leave(line.date, line.employee_id.id) or self._check_holiday(line.date):
                    line.ot_double_hours = line.worked_hours
                else:
                    line.ot_double_hours = 0
            else:
                line.ot_double_hours = 0

    def _check_holiday(self, date):
        """check for global holiday"""
        global_leave = self.env['resource.holidays'].search([('start_date', '>=', str(date)), ('end_date', '<=', str(date))])
        if global_leave:
            return True
        else:
            return False

    def _check_leave(self, date, employee_id):
        """Check for leave of the meployee"""
        hr_leave = self.env['hr.leave'].search([('request_date_from', '>=', str(date)), ('request_date_to', '<=', str(date)), ('employee_id', '=', employee_id), ('state', 'in', ['confirm', 'validate1', 'validate'])])
        if hr_leave:
            return True
        else:
            return False

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                pass
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    pass

    @api.depends('check_in')
    def _get_in_time(self):
        """get in time"""
        for line in self:
            if line.check_in:
                check_in = fields.Datetime.to_string(
                    fields.Datetime.from_string(line.check_in) + timedelta(hours=5, minutes=30))
                line.in_time = convert_to_float(check_in)
            else:
                line.in_time = 0

    @api.depends('check_out')
    def _get_out_time(self):
        """get out time"""
        for line in self:
            if line.check_out:
                check_out = fields.Datetime.to_string(
                    fields.Datetime.from_string(line.check_out) + timedelta(hours=5, minutes=30))
                line.out_time = convert_to_float(check_out)
            else:
                line.out_time = 0

    @api.depends('check_in', 'check_out')
    def _get_working_time(self):
        """get working time"""
        for line in self:
            if line.check_in and line.check_out:
                if line.check_out > line.check_in:
                    check_in = fields.Datetime.to_string(
                        fields.Datetime.from_string(line.check_in) + timedelta(hours=5, minutes=30))
                    check_out = fields.Datetime.to_string(
                        fields.Datetime.from_string(line.check_out) + timedelta(hours=5, minutes=30))
                    line.working_time = convert_to_float(check_out) - convert_to_float(check_in)
                else:
                    line.working_time = 0





