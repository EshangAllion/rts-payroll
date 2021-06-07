from odoo import fields, models, api


class SmsGatewayUrl(models.Model):
    _name = 'sms.gateway.url'

    name = fields.Char('Url')
    username = fields.Char('Username')
    password = fields.Char('Password')
    sender_id = fields.Char('Sender ID')
    dr = fields.Selection([('1', '1')], 'Delivery report enabled')


class SmsGatewayConfig(models.Model):
    _name = 'sms.gateway.config'

    name = fields.Selection([('order_create', 'Create Order SMS'), ('order_confirm', 'Confirm Order SMS')], string="Name")
    body = fields.Text(string="Text Body")
    url_id = fields.Many2one('sms.gateway.url', string="URL")
    url = fields.Char('Url', related='url_id.name')
    username = fields.Char('Username', related='url_id.username')
    password = fields.Char('Password', related='url_id.password')
    sender_id = fields.Char('Sender ID', related='url_id.sender_id')
    dr = fields.Selection([('1', '1')], 'Delivery report enabled', related='url_id.dr')
