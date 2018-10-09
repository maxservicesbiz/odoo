# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class ResCountryLocality(models.Model):
    _name = 'res.country.locality'
    _rec_name = 'name'

    code = fields.Char(string=_("Code"), required=True)
    name = fields.Char(string=_("Name"), required=True)
    state_id = fields.Many2one(comodel_name='res.country.state', string=_("State"), required=True)
