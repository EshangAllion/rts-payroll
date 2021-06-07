from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import UserError


class InheritSaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        """SMS Created when creating a sales order"""
        return_obj = super(InheritSaleOrder, self).create(vals)
        self.validate_phone_number(return_obj.partner_id.mobile)
        if return_obj.partner_id.mobile:
            sms = self.env['sms.log'].create({
                'name': return_obj.partner_id.id,
                'sms_gateway_url': self.env['sms.gateway.config'].search([('name', '=', 'order_create')], limit=1).id,
                'sale_order_id': return_obj.id,
                'mobile_number': return_obj.partner_id.mobile,
                'date': str(datetime.now().date())
            })
            sms.send_sms()
        return return_obj

    def action_confirm(self):
        """SMS Created when confirming a sales order"""
        return_obj = super(InheritSaleOrder, self).action_confirm()
        self.validate_phone_number(self.partner_id.mobile)
        if self.partner_id.mobile:
            sms = self.env['sms.log'].create({
                'name': self.partner_id.id,
                'sms_gateway_url': self.env['sms.gateway.config'].search([('name', '=', 'order_confirm')], limit=1).id,
                'sale_order_id': self.id,
                'mobile_number': self.partner_id.mobile,
                'date': str(datetime.now().date())
            })
            sms.send_sms()
        return return_obj

    def validate_phone_number(self, mobile):
        """validating phone number"""
        if mobile:
            if len(mobile) != 10:
                raise UserError("Invalid mobile number")

