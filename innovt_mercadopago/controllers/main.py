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

import pprint
import logging
from werkzeug import urls, utils
import threading

from odoo import http, _ , fields

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)

import mercadopago
import json
from datetime import datetime, timedelta
import pytz
import pprint

class InnovtMercadopagoController(http.Controller):
    
    _url_success  =  '/payment/mercadopago/success'
    _url_failure  =  '/payment/mercadopago/failure'
    _url_pending  =  '/payment/mercadopago/pending'
    _url_notify  =  '/payment/mercadopago/notify' 
    
    def datetime_iso_8601(self, dt, tz):
        dt_timestamp = datetime.timestamp(dt)
        dt_iso = datetime.fromtimestamp(dt_timestamp,  pytz.timezone(tz))
        return "{}{}".format(dt.isoformat()[:23], dt_iso.isoformat()[-6:])
    
    def mercadopago_validate_data(self, data):
        res = http.request.env['payment.transaction'].sudo().form_feedback( data, 'mercadopago')
        return res
        
    @http.route(['/payment/mercadopago'], type='http', auth='public')
    def mercadopago(self, **post):
        
        ptx = http.request.env['payment.transaction'].sudo().search(
            [('reference','=', post.get('mp_item_number'))]
        )
        if not len(ptx):
            raise ValidationError("Not found Mercadopago payment acquired")
        mp =mercadopago.MP(ptx.acquirer_id.mercadopago_client_id, ptx.acquirer_id.mercadopago_client_secret)
        if post.get("mp_environment") == 'test':
            mp.sandbox_mode(enable=True)
        tz = ptx.env.context.get('tz') or  'America/Mexico_City'
        dt  = datetime.utcnow()
        expiration_date_from = self.datetime_iso_8601(dt, tz)
        expiration_date_to =   self.datetime_iso_8601(dt + timedelta(days=1), tz)
        
        preference = {
            "external_reference": post.get("mp_item_number"),
            "payer": {
                "name": "{} {}".format(post.get("mp_billing_first_name"), post.get("mp_billing_last_name")),
                "email": post.get("mp_billing_email"),
                "phone":{
                    "number": post.get("mp_billing_phone")
                 },
                "address": {
                    "street_name": post.get("mp_billing_address"),
                    #"street_number": "",
                    "zip_code": post.get("mp_billing_zip"),
                }
            },
            "auto_return": "approved",
            "items": [
                {
                    "title": post.get("mp_item_name"),
                    "quantity": 1,
                    "currency_id": post.get("mp_currency_id"),
                    "unit_price": float(post.get("mp_amount"))
                }
            ],
            "back_urls": {
		            "success": post.get('mp_url_success'),
		            "failure": post.get('mp_url_failure'),
		            "pending": post.get('mp_url_pending')
            },
            "notification_url": post.get("mp_url_notify"),
            "expires": True,
            "expiration_date_from": expiration_date_from,
            "expiration_date_to": expiration_date_to

        }
        _logger.info('MercadoPago preference %s', pprint.pformat(preference))
        preferenceResult = mp.create_preference(preference)
        if 'status' in preferenceResult and  preferenceResult.get('status') == 201:
            preferenceResponse = preferenceResult.get('response')
            if post.get("mp_environment") == 'prod':
                url_pay =  preferenceResponse.get("init_point")
                ptx.update({'mercadopago_tx_id': preferenceResponse.get('id')})
            else:
                url_pay =  preferenceResponse.get("sandbox_init_point")
            print(json.dumps(preferenceResult, indent=4))
        else:
            error_msg = json.dumps(preferenceResult, indent=2)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return utils.redirect(url_pay)

    @http.route(['/payment/mercadopago/failure'], type='http', auth='public')
    def mercadopago_failure(self, **post):
        _logger.info('Beginning MercadoPago route failure with post data %s', pprint.pformat(post))
        """
            Mercadopago 
            Method : GET
            Query  : payment/mercadopago/failure?collection_id=null&collection_status=null&preference_id=396501523-5ba52799-3855-4a3c-8fb2-9bcfbafe4f46&external_reference=SO034&payment_type=null&merchant_order_id=null
        """
        if post.get('collection_status') == 'null':
            post.update({'collection_status':'cancelled'})
        res = self.mercadopago_validate_data(post)
        return utils.redirect('/shop/payment/validate')
    
    @http.route(['/payment/mercadopago/success'], auth='public')
    def mercadopago_success(self, **post):
        """
        Method: GET 
        Query: /payment/mercadopago/success?collection_id=20189415&collection_status=approved&preference_id=396501523-f63f152f-f081-4cb3-8dba-d098a8a0fc4f&external_reference=SO045&payment_type=debit_card&merchant_order_id=1118140280 
        """
        _logger.info('Beginning MercadoPago route success with post data %s', pprint.pformat(post))
        res = self.mercadopago_validate_data(post)
        return utils.redirect('/shop/payment/validate')
    
    @http.route(['/payment/mercadopago/pending'], auth='public')
    def mercadopago_pending(self, **post):
        """
        Method: GET
        Query: /payment/mercadopago/pending?collection_id=20189619&collection_status=pending&preference_id=396501523-552a7d2d-e458-415d-b754-8fb6bcad8c7f&external_reference=SO049&payment_type=bank_transfer&merchant_order_id=1118149111
        """
        _logger.info('Beginning MercadoPago route pending with post data %s', pprint.pformat(post))
        res = self.mercadopago_validate_data(post)
        return utils.redirect('/shop/payment/validate')
        
    @http.route(['/payment/mercadopago/notify'], type='json', auth='public', csrf=False)
    def mercadopago_notify(self, **post):
        """
        Method: GET
        Query: 
            /payment/mercadopago/notify?id=1118062804&topic=merchant_order
            /payment/mercadopago/notify?data.id=20185627&type=payment
        """
        params = http.request.httprequest.args.to_dict()
        _logger.info('Beginning MercadoPago route notify with post data %s', pprint.pformat(post))
        _logger.info('Beginning MercadoPago route notify with post params %s', pprint.pformat(params))
        topic = params.get('topic', params.get('type', '')) 
        id = params.get('id', params.get('data.id', ''))
        pa = http.request.env['payment.acquirer'].sudo().search([('provider','=','mercadopago')])
        if len(pa):
            mp =mercadopago.MP(pa.mercadopago_client_id, pa.mercadopago_client_secret)
            if pa.environment == 'test':
                mp.sandbox_mode(enable=True)
            data = {}
            if topic == 'merchant_order':
                merchant_order =mp.get("/merchant_orders/"+id)
                if merchant_order.get('status', 0) == 200:
                    merchant_response = merchant_order.get('response')
                    data.update({
                        'preference_id': merchant_response.get('preference_id'),
                        'external_reference': merchant_response.get('external_reference')
                    })
                logging.info(pprint.pformat(merchant_order, indent=2))
            elif topic == 'payment':
                payment = mp.get("/v1/payments/"+id)
                logging.info(pprint.pformat(payment, indent=2))
        return ''