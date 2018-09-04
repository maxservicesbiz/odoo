# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class WayPay(models.Model):
    _name = 'payment.form'
    _rec_name = 'display_name'

    code = fields.Char(string=_("Code way to pay"), help=_("Code provided by SAT"), required=True)
    name = fields.Char(string=_("Name way to pay"), required=True)
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name")

    @api.multi
    def _compute_display_name(self):
        for row in self:
            row.display_name = row.code + ' - ' + row.name
