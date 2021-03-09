#! -*- coding: utf-8 -*-

from odoo import models, fields, _, api

INNOVT_INNOV_API_KEYS = [
    'innovt_client.msc_api_client_id',
    'innovt_client.msc_api_client_secret',
    'innovt_client.msc_api_mode',
]


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    msc_api_client_id = fields.Char(string=_("Client id"))
    msc_api_client_secret = fields.Char(string=_("Client secret"))
    msc_api_mode = fields.Boolean(string=_("Sandbox"))

    @api.model
    def key2field(self, key=""):
        return key[key.find('.') + 1:]

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        if isinstance(res, dict):
            params = self.env['ir.config_parameter'].sudo()
            for item in INNOVT_INNOV_API_KEYS:
                res.update({self.key2field(item): params.get_param(item, default=False)})
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        for item in INNOVT_INNOV_API_KEYS:
            params.set_param(item, getattr(self, self.key2field(item)))

    @api.model
    def get_innov_api_settings(self):
        values = self.get_values()
        res = {}
        for item in INNOVT_INNOV_API_KEYS:
            _field = self.key2field(item)
            _value = values[_field]
            if _field == 'msc_api_mode':
                if _value:
                    _value = 'sandbox'
                else:
                    _value = 'live'
            _field = _field.replace('msc_api_', '')
            res.update({_field: _value})
        return res

    @api.model
    def get_innov_settings_api(self):
        """
         Not is recommend use this method in the next update  is removed.
        :return:
        """
        params = self.env['ir.config_parameter'].sudo()
        msc_api_client_id = params.get_param('innovt_client.msc_api_client_id', default=False)
        msc_api_client_secret = params.get_param('innovt_client.msc_api_client_secret', default=False)
        msc_api_mode = params.get_param('innovt_client.msc_api_mode', default=False)
        return {
            'mode': 'sandbox' if msc_api_mode else 'live',
            'client_id': msc_api_client_id,
            'client_secret': msc_api_client_secret
        }
