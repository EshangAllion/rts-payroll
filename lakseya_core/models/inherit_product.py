from odoo import fields, models, api


class InheritProductTemplate(models.Model):
    _inherit = 'product.template'

    employee_ids = fields.Many2many('hr.employee', string="Specialist Person")