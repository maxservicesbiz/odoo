# -*- coding: utf-8 -*-
# © Yonn, Xyz. All rights reserved.

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    client_id = fields.Char(string=_("Client Id"))
    client_secret = fields.Char(string=_("Client secret"))
   #token = fields.Text(string=_("Infinity token"))
    mode = fields.Boolean(string=_("Test mode"))
