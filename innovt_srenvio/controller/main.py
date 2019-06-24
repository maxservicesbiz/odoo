
# -*- coding: utf-8 -*-
#   Copyright (C) 2019  MAXS
#   
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery
from odoo.addons.innovt_srenvio.models.srenvio_request import SrenvioProvider
import logging
import pprint
_logger = logging.getLogger(__name__)

class WebsiteSaleSrenvioDelivery(WebsiteSaleDelivery):
    
    
    @http.route(['/shop/srenvio/shipments'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def shop_srenvio_shipments(self, **post):
        order = request.website.sale_get_order()
        carrier_id = int(post['carrier_id'])
        #currency = order.currency_id
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        if carrier.delivery_type == 'srenvio':
            se = SrenvioProvider(carrier)
            qoutations = se.srenvio_quotations(order)
        else:
            qoutations = []
        return {
            'status': len(qoutations)>1,
            'qoutations': qoutations,
            'carrier_id': carrier_id
        }
    @http.route(['/shop/update_carrier'], type='json', auth='public', methods=['POST'], website=True, csrf=False)
    def update_eshop_carrier(self, **post):
        carrier_id = int(post['carrier_id'])
        carrier = request.env['delivery.carrier'].sudo().browse(carrier_id)
        if carrier.delivery_type == 'srenvio':
            order = request.website.sale_get_order()
            currency = order.currency_id
            provider = post.get('provider', False)
            service_level_code = post.get('service_level_code', False)
            if provider and service_level_code:
                order.with_context(provider=provider,
                                  service_level_code=service_level_code
                                  )._check_carrier_quotation(force_carrier_id=carrier_id)
                return {'status': order.delivery_rating_success,
                    'error_message': order.delivery_message,
                    'carrier_id': carrier_id,
                    'new_amount_delivery': self._format_amount(order.delivery_price, currency),
                    'new_amount_untaxed': self._format_amount(order.amount_untaxed, currency),
                    'new_amount_tax': self._format_amount(order.amount_tax, currency),
                    'new_amount_total': self._format_amount(order.amount_total, currency),
                }
        return WebsiteSaleDelivery.update_eshop_carrier(self, **post)