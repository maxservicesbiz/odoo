# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    carrier_delivery_type = fields.Selection(related="carrier_id.delivery_type")
    srenvio_provider = fields.Char(help=_("SrEnvio Proveedor"))
    srenvio_service_level_code = fields.Char(help=_("SrEnvio Codigo de servicio"))
    
    
