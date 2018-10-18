# -*- coding: utf-8 -*-
# © Yonn, Xyz. All rights reserved.
from odoo import models, fields, api, _


class ResBank(models.Model):
    _inherit = 'res.bank'

    vat = fields.Char(string=_("VAT"))
