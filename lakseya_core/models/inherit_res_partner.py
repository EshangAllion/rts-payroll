from odoo import fields, api, models
from odoo.exceptions import UserError


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    code = fields.Char('Code', copy=False)

    def name_get(self):
        """overiding default get function"""
        result = []
        for partner in self:
            if partner.code:
                name = partner.code + " - " + partner.name
            else:
                name = partner.name
            result.append((partner.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Updated respartner search_name, so that it can be searched by code"""
        results_obj = super(InheritResPartner, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)
        if not results_obj:
            results_obj = self._search([('code', 'ilike', name)] + args, limit=limit, access_rights_uid=name_get_uid)
            return self.browse(results_obj).name_get()
        return results_obj

    @api.model
    def create(self, vals):
        """overding create core method"""
        create_obj = super(InheritResPartner, self).create(vals)
        if not create_obj.code and create_obj.customer_rank >= 1:
            if not self.env.company.partner_sequence_id:
                raise UserError('Please configure a sequence for customers in the company configurations.')
            create_obj.code = self.env.company.partner_sequence_id.next_by_id()
        return create_obj

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        """removed validation"""
        if self.phone:
            pass

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        """removed validation"""
        if self.mobile:
            pass


class InheritResCompany(models.Model):
    _inherit = 'res.company'

    partner_sequence_id = fields.Many2one('ir.sequence', string="Customer Sequence")
