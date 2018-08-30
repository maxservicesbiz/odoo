# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class Country(models.Model):
    _inherit = 'account.fiscal.position'

    code = fields.Char(string=_("Code"), help=_("Code SAT"))
