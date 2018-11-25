#! -*- coding: utf-8 -*-

from odoo import models, fields, _, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    msc_api_client_id = fields.Char(string=_("Client id"))
    msc_api_client_secret = fields.Char(string=_("Client secret"))
    msc_api_mode = fields.Boolean(string=_("Sandbox"))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        if isinstance(res, dict):
            params = self.env['ir.config_parameter'].sudo()
            msc_api_client_id = params.get_param('innovt_client.msc_api_client_id', default=False)
            msc_api_client_secret = params.get_param('innovt_client.msc_api_client_secret', default=False)
            msc_api_mode = params.get_param('innovt_client.msc_api_mode', default=False)
            res.update({
                'msc_api_client_id': msc_api_client_id,
                'msc_api_client_secret': msc_api_client_secret,
                'msc_api_mode': msc_api_mode
            })
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param("innovt_client.msc_api_client_id", self.msc_api_client_id)
        params.set_param("innovt_client.msc_api_client_secret", self.msc_api_client_secret)
        params.set_param("innovt_client.msc_api_mode", self.msc_api_mode)

    @api.model
    def get_innov_settings_api(self):
        params = self.env['ir.config_parameter'].sudo()
        msc_api_client_id = params.get_param('innovt_client.msc_api_client_id', default=False)
        msc_api_client_secret = params.get_param('innovt_client.msc_api_client_secret', default=False)
        msc_api_mode = params.get_param('innovt_client.msc_api_mode', default=False)
        return {
            'mode': 'sandbox' if msc_api_mode else 'live',
            'client_id': msc_api_client_id,
            'client_secret': msc_api_client_secret
        }
