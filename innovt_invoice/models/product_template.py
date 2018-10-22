# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_code_id = fields.Many2one(comodel_name='product.code', string=_('Product code'))
    product_unit_id = fields.Many2one(comodel_name='product.unit', string=_('Product unit'))
