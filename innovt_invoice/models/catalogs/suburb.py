# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class ResCountrySuburb(models.Model):
    _name = 'res.country.suburb'
    _rec_name = 'name'

    code = fields.Char(string=_("Code locality"), help=_("Code provided by SAT"), required=True)
    name = fields.Char(string=_("Name locality"), required=True)
    zip_code = fields.Char(string=_("Zip code"), required=True)
