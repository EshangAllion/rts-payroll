from odoo import models, api, _, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    so_step_bypass = fields.Boolean(string="Invoice Auto Create")
