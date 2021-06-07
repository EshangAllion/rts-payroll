from odoo import fields, models, api


class ResourceHolidays(models.Model):
    _name = 'resource.holidays'

    name = fields.Char(string='Reason')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')