# -*- coding: utf-8 -*-
import pprint
import logging
from werkzeug import urls, utils

from odoo import http, _ , fields
from odoo.http import request

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
    
    
    @http.route(['/payment/mercadopago/success'], type='http', auth='public')
    def mercadopago_success(self, **post):
        _logger.info('Beginning MercadoPago route success with post data %s', pprint.pformat(post))

    @http.route(['/payment/mercadopago/pending'], type='http', auth='public')
    def mercadopago_pending(self, **post):
        _logger.info('Beginning MercadoPago route pending with post data %s', pprint.pformat(post))        
        
    @http.route(['/payment/mercadopago/notify'], type='http', auth='public')
    def mercadopago_notify(self, **post):
        _logger.info('Beginning MercadoPago route notify with post data %s', pprint.pformat(post))     