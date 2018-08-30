# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class ProductCode(models.Model):
    _name = 'product.code'
    _rec_name = 'display_name'

    code = fields.Char(string=_("Code product code"), help=_("Code provided by SAT"), required=True)
    name = fields.Char(string=_("Name product code"), required=True)

    display_name = fields.Char(string=_("Rec name product code"), compute="_compute_display_name")

    @api.depends('code','name')
    @api.multi
    def _compute_display_name(self):
        for row in self:
            row.display_name = row.code + " - " + row.name
