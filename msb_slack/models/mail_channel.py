# -*- coding: utf-8 -*-
#   Copyright (C) 2020  Max Services Biz
from odoo import models, fields, api, _


#

class MSBMailChannel(models.Model):
    _inherit = 'mail.channel'
    slack_model_ids = fields.Many2many('ir.model', 'channel_model_rel' ,'model_id', 'channel_id', string='Slack Models')

class MSBMailChannel(models.Model):
    _inherit = 'res.partner'
    slack_id = fields.Char(string='Slack ID')

class MSBMailChannel(models.Model):
    _inherit = 'res.users'
    slack_id = fields.Char(string='Slack ID', related='partner_id.slack_id', inherited=True)


class MSBSlackResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    msb_slack_slack_webhook_url = fields.Char('Slack Webhook URL',  config_parameter='msb_slack_slack_webhook_url')
   
    @api.model
    def get_values(self):
        res = super(MSBSlackResConfigSettings, self).get_values()        
        params = self.env['ir.config_parameter'].sudo()
        res.update({"msb_slack_slack_webhook_url": params.get_param("msb_slack_slack_webhook_url", default=False)})
        return res

    @api.multi
    def set_values(self):
        super(MSBSlackResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()    
        params.set_param("msb_slack_slack_webhook_url", self.msb_slack_slack_webhook_url)