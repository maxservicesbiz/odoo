# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fiscal_residence = fields.Many2one(comodel_name='res.country', string=_("Fiscal residence"))
    tax_identity_registration_number = fields.Char(string=_("Tax identity registration number"))
    cfdi_use_id = fields.Many2one(comodel_name='cfdi.use', string=_("Merchandise use"))


