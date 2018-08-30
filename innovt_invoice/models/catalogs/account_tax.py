# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class AccountTax(models.Model):
    _inherit = 'account.tax'

    type_tax_id = fields.Many2one(comodel_name='type.tax', string=_("Type tax"))
    type_factor_id = fields.Many2one(comodel_name='type.factor', string=_("Type factor"))


class TypeTax(models.Model):
    _name = 'type.tax'
    _rec_name = 'display_name'

    code = fields.Char(string=_("Code type of tax"))
    name = fields.Char(string=_("Name type of tax"))
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name")

    @api.multi
    def _compute_display_name(self):
        for row in self:
            row.display_name = row.code + ' - ' + row.name


class TypeFactor(models.Model):
    _name = 'type.factor'
    _rec_name = 'display_name'

    code = fields.Char(string=_("Code type of factor"))
    name = fields.Char(string=_("Name type of factor"))
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name")

    @api.multi
    def _compute_display_name(self):
        for row in self:
            row.display_name = row.code + ' - ' + row.name
