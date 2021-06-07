from odoo import fields, models, api
from odoo.exceptions import UserError


class ServiceLog(models.TransientModel):
    _name = 'service.log'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    sale_order_id = fields.Many2one('sale.order', string='Job Number')
    product_id = fields.Many2one('product.product', string='Service')
    product_product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string="Quantity", default=1)
    product_type = fields.Selection([('service', 'Service'), ('product', 'Product')], string="Product Type", default='service')
    description = fields.Char('Service Description')
    price = fields.Float("Price")

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """Onchange domain for product_id according to employee_id"""
        sale_orders = self.env['sale.order'].sudo().search([('state', 'in', ['draft', 'sent'])])
        self.department_id = self.sudo().employee_id.department_id.id
        return {'domain': {'product_id': [('employee_ids', 'in', self.sudo().employee_id.id), ('type', '=', 'service')], 'sale_order_id': [('id', 'in', sale_orders.ids)]}}

    def submit_service_log(self):
        """Creating the service log in particular sale order"""
        if self.price <= 0:
            raise UserError('Price should be greater than 0.')
        product_id = self.sudo().product_id.id if self.sudo().product_type == 'service' else self.sudo().product_product_id.id
        uom = self.sudo().product_id.uom_id.id if self.sudo().product_type == 'service' else self.sudo().product_product_id.uom_id.id
        self.env['sale.order.line'].sudo().create({
            'order_id': self.sale_order_id.id,
            'product_id': None if product_id == False else product_id,
            'name': self.description,
            'employee_id': self.employee_id.id,
            'department_id': self.department_id.id,
            'price_unit': self.price,
            'product_uom_qty': 1 if self.product_type == 'service' else self.quantity,
            'product_uom': None if uom == False else uom
        })








