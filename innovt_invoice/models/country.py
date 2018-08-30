# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class Country(models.Model):
    _inherit = 'res.country'

    code3 = fields.Char(string=_("Code 3"), help=_("Three letter codes ISO ALPHA-3 MEX"))
