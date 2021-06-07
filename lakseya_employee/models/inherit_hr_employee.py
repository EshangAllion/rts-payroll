from odoo import fields, models, api, _


class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_no = fields.Char("Employee Number")
    join_date = fields.Date("Join Date")