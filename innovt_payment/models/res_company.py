# -*- coding: utf-8 -*-
# © Yonn, Xyz. All rights reserved.
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    payment_series = fields.Char(string=_("Payment series"))
