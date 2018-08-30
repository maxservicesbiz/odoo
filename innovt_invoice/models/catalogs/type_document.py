# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class TypeDocument(models.Model):
    _name = 'type.document'
    _rec_name = 'display_name'

    code = fields.Char(string=_("Code type of document"), help=_("Code provided by SAT"), required=True)
    name = fields.Char(string=_("Name type of document"), required=True)
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name")

    @api.multi
    def _compute_display_name(self):
        for row in self:
            row.display_name = row.code + ' - ' + row.name
