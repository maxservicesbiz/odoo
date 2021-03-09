from odoo import models, fields, _, api

CT_API_KEYS = [
    'innovt_dropshipping_ct.ct_api_url',
    'innovt_dropshipping_ct.ct_api_email',
    'innovt_dropshipping_ct.ct_api_user',
    'innovt_dropshipping_ct.ct_api_rfc',
    'innovt_dropshipping_ct.ct_warehouses'
]

CT_FTP_KEYS = [
    'innovt_dropshipping_ct.ct_ftp_host',
    'innovt_dropshipping_ct.ct_ftp_user',
    'innovt_dropshipping_ct.ct_ftp_password',
]

class InnovtDropshippingCTResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ct_api_url = fields.Char(string="Kibana URl")
    ct_api_email = fields.Char(string="Kibana Usuario")
    ct_api_user = fields.Char(string="Kibana Contraseña")
    ct_api_rfc = fields.Char(string="Kibana Contraseña")

    ct_ftp_host = fields.Char(string="Kibana Contraseña")
    ct_ftp_user = fields.Char(string="Kibana Contraseña")
    ct_ftp_password = fields.Char(string="Kibana Contraseña")
    ct_warehouses = fields.Char(string="Kibana Contraseña")

    @api.model
    def key2field(self, key=""):
        return key[key.find('.') + 1:]

    @api.model
    def get_values(self):
        res = super(InnovtDropshippingCTResConfigSettings, self).get_values()
        if isinstance(res, dict):
            params = self.env['ir.config_parameter'].sudo()
            for item in CT_API_KEYS + CT_FTP_KEYS:
                res.update({self.key2field(item): params.get_param(item, default=False)})
        return res

    @api.multi
    def set_values(self):
        super(InnovtDropshippingCTResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        for item in CT_API_KEYS + CT_FTP_KEYS:
            params.set_param(item, getattr(self, self.key2field(item)))
    
    @api.model
    def get_ct_api(self):

        values = self.get_values()
        res = {}
        for item in CT_API_KEYS + CT_FTP_KEYS:
            _field = self.key2field(item)
            _value = values[_field]           
            res.update({_field: _value})
        return res