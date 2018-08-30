# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, _


class ResCountryMunicipality(models.Model):
    _name = 'res.country.municipality'
    _rec_name = 'name'

    code = fields.Char(string=_("Code municipality"), help=_("Code provided by SAT"), required=True)
    name = fields.Char(string=_("Name municipality"), required=True)
    state_id = fields.Many2one(comodel_name='res.country.state', string=_("State"), required=True)
