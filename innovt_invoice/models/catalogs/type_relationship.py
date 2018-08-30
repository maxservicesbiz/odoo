# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class TypeRelationship(models.Model):
    _name = 'type.relationship'
    _rec_name = 'display_name'

    code = fields.Char(string=_("Code type of relationship"), help=_("Code provided by SAT"), required=True)
    name = fields.Char(string=_("Name type of relationship"), required=True)
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name")

    @api.multi
    def _compute_display_name(self):
        for row in self:
            row.display_name = row.code + ' - ' + row.name
