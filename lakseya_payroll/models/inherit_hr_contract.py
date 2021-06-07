from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import UserError


class InheritHrContract(models.Model):

    _inherit = 'hr.contract'

    consolidated = fields.Float(string="Consolidated", track_visibility='always')
    budget_1 = fields.Float(string="Budget Allowance 01", track_visibility='always')
    budget_2 = fields.Float(string="Budget Allowance 02", track_visibility='always')
    travelling = fields.Float(string="Travelling", track_visibility='always')
    production_incentive = fields.Float(string="Production Incentive", track_visibility='always')
    stamp_fee = fields.Float(string="Stamp Fee", track_visibility='always')
    welfare = fields.Float(string="Staff Welfare", track_visibility='always')
    salary_advance = fields.Float(string="Salary Advance", track_visibility='always')
    festival_advance = fields.Float(string="Festival Advance", track_visibility='always')
    staff_loan = fields.Float(string="Staff Loan", track_visibility='always')
    credit_bill = fields.Float(string="Credit Bill", track_visibility='always')
    other = fields.Float(string="Other Allowance", track_visibility='always')
    other_ded = fields.Float(string="Other Deduction", track_visibility='always')
    initials = fields.Char(string='Initials')
    epf_number = fields.Integer(string='EPF Number')
    wage = fields.Monetary('Basic Salary', required=True, tracking=True, help="Employee's monthly gross wage.")



