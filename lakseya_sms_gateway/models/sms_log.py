from odoo import fields, models, api
import requests
import json


class SmsLog(models.Model):
    _name = 'sms.log'

    name = fields.Many2one('res.partner', string="Customer")
    sms_gateway_url = fields.Many2one('sms.gateway.config', string="Gateway Details")
    body = fields.Text(string="Text Body", related='sms_gateway_url.body')
    state = fields.Selection([('success', 'Success'), ('failed', 'Failed')], 'Status')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    mobile_number = fields.Char('Mobile Number')
    response = fields.Char('Response')
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string="Company")

    def send_sms(self):
        """Sending th SMS, by creating the msg body"""
        if self.sale_order_id.company_id.id in [1]:
            body = {
                "username": self.sms_gateway_url.username,
                "password": self.sms_gateway_url.password,
                "src": self.sms_gateway_url.sender_id,
                "dst": self.mobile_number,
                "msg": self.body % self.sale_order_id.name if not self.sms_gateway_url.name == 'order_confirm' else self.body % (self.sale_order_id.name, str(self.name.total_due)),
                "dr": self.sms_gateway_url.dr,
                "company_id": self.sale_order_id.company_id.id
            }
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            response = requests.post(url=self.sms_gateway_url.url, headers=headers, data=body)
            if response.status_code == 200:
                self.write({
                    'state': 'success',
                    'response': response.text
                })
            else:
                self.write({
                    'state': 'failed',
                    'response': response.text
                })