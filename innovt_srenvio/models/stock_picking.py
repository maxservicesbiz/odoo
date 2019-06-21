# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    srenvio_tracking_ref = fields.Char()
    srenvio_label_id = fields.Integer()
    srenvio_shipping_id = fields.Integer()