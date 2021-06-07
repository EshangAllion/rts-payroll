from odoo import fields, models, api
from odoo.exceptions import UserError


class CommissionSlabConfiguration(models.Model):
    _name = 'commission.slab.configuration'

    name = fields.Char('Commission Name')
    employee_ids = fields.Many2many('hr.employee', string="Allowed Employee")
    department_id = fields.Many2one('hr.department', string='Department')
    commission_type = fields.Selection([('percentage', 'Percentage'), ('fix_mount', 'Fixed Amount')], string='Commission Type')
    slab_config_ids = fields.One2many('slab.configuration', 'line_id')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        """Validation when creating records"""
        return_obj = super(CommissionSlabConfiguration, self).create(vals)
        # for items in return_obj.employee_ids:
        #     exist = self.search([('employee_ids', 'in', items.id), ('id', '!=', return_obj.id)])
        #     if exist:
        #         raise UserError("There's already a commission for the employee")
        if not return_obj.slab_config_ids:
            raise UserError("There should be at least on slab configuration line.")
        return return_obj


class SlabConfiguration(models.Model):
    _name = 'slab.configuration'

    revenue_start_amount = fields.Float(string="Revenue Start Amount")
    revenue_end_amount = fields.Float(string="Revenue End Amount")
    amount = fields.Float(string="Percentage/Fix Amount")
    line_id = fields.Many2one('commission.slab.configuration')

    @api.model
    def create(self, vals):
        """Validation when creating records"""
        return_obj = super(SlabConfiguration, self).create(vals)
        if return_obj.revenue_start_amount >= return_obj.revenue_end_amount:
            raise UserError("Revenue Start amount should be greater than revenue end amount.")
        if return_obj.amount <= 0:
            raise UserError("Percentage should be greater than 0.")
        all_line_items = self.env['slab.configuration'].search([('line_id', '=', return_obj.line_id.id)])
        for item in all_line_items:
            if not item.id == return_obj.id:
                if item.revenue_start_amount <= return_obj.revenue_start_amount <= item.revenue_end_amount or item.revenue_start_amount <= return_obj.revenue_end_amount <= item.revenue_end_amount:
                    raise UserError("Line amounts cannot be overlapped or duplicated")
        return return_obj

