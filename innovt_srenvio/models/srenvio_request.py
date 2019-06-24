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
import werkzeug
import requests
import logging
import pprint
import base64
_logger = logging.getLogger(__name__)
from odoo.exceptions import  ValidationError

class SrenvioProvider(object):
    
    def __init__(self, carrier):
        if carrier.prod_environment: 
            self.url =  ""
        else:
            self.url = "https://api-demo.srenvio.com/v1/"
        self.token = carrier.srenvio_token
        self.carrier = carrier
    

    def _srenvio_request_check_errors(self, result):
        if not isinstance(result, dict) :
            result = {}
        if 'errors' in result or \
         'error_message' in result.get('data',{}).get('attributes', {}) or \
          result.get('data',{}).get('attributes', {}).get('status',"") == 'ERROR':
            raise Exception("Los datos de la peticion son incrrectos")
            
    def _srenvio_request(self, url, data, **kwargs):

        headers = {
            'Authorization': 'Token token=%s' % self.token
        }
        method = kwargs.get('method', 'POST')
        _logger.info('Beginning SrEnvio request %s ', url)
        _logger.info('Data SrEnvio request %s ', data)
        if method == 'POST':
            response = requests.post(url, json=data, headers=headers)        
        status = response.status_code
        try:
            result = response.json()
            _logger.info('Response %s %s', status, pprint.pformat(result))
            self._srenvio_request_check_errors(result)
            return True, result
        except Exception as e :
            _logger.info('Exception msg: %s ', e)
            _logger.info('Response text: %s %s', status, pprint.pformat(response.text))
            msg  = "Estatus: %s Msg: Fallo la petición intente de nuevo por favor." % status
            if 600 > status < 500:
                msg =  response.text
            return False, msg
    
    def srenvio_quotations(self, order):
        url = werkzeug.urls.url_join(self.url, "quotations")
        shipping = order.partner_shipping_id
        company = order.company_id
        package = self.srenvio_cal_package(order)
        data = {
            "zip_from": shipping.zip,
            "zip_to": company.zip,
            "parcel": {
                "weight": package.get('weight'),
                "height": package.get('package_height'),
                "width": package.get('package_width'),
                "length": package.get('package_length'),
            }
        }
        ok, quotations = self._srenvio_request(url, data)
        if ok:
            return quotations
        return []
      
    def srenvio_shipments(self, order):
        if order.srenvio_provider and order.srenvio_service_level_code:
            company = order.company_id
            shipping = order.partner_shipping_id
            contents = ""
            for order_line in order.order_line:
                contents += order_line.name
                break
            package = self.srenvio_cal_package(order)
            data =  {
                "address_from": {
                    "province": company.state_id.name or "",
                    "city": company.city or "",
                    "name": company.name or "",
                    "zip": company.zip,
                    # country code 3 chars
                    "country": company.country_id.code,
                    "address1": company.street or  "",
                    "company": company.name or "",
                    "address2": company.street2,
                    "phone": company.phone,
                    "email": company.email
                },
                "parcels": [{
                    "weight": package.get('weight'),
                    "distance_unit": self.carrier.srenvio_package_dimension_unit,
                    "mass_unit": self.carrier.srenvio_package_weight_unit,
                    "height": package.get('package_height'),
                    "width": package.get('package_width'),
                    "length": package.get('package_length')
                    }],
                "address_to": {
                    "province": shipping.state_id.code or "",
                    "city": shipping.city or "",
                    "name": shipping.name,
                    "zip": shipping.zip,
                    # Same case adove
                    "country": shipping.country_id.code,
                    "address1": shipping.street or "",
                    "company": shipping.name if shipping.company_type == 'person' else shipping.parent_id.name,
                    "address2": shipping.street2,
                    "phone": shipping.phone,
                    "email": shipping.email,
                    "contents": contents
                }
            }
            url = werkzeug.urls.url_join(self.url, "shipments")
            ok, shipments = self._srenvio_request(url, data)
            if ok:
                shipments_data  = shipments.get('data')
                shipments_included  = shipments.get('included')
                for include in shipments_included:
                    attributes = include.get('attributes', {})
                    if attributes.get('provider', "") == order.srenvio_provider and attributes.get("service_level_code","") == order.srenvio_service_level_code:
                            return {"shipping_id": shipments_data.get("id"), **include}
                raise ValidationError(_("El Proveedor con el codigo de servicio no fue encontrado en el envio creado."
                                        "Intente de nuevo o cambie de Proveedor."))
            raise ValidationError(_("Fallo al generar el envio, intente de nuevo por favor. \n %s" % shipments))
        raise ValidationError(_("Capture los datos de SrEnvio Proveedor  y Codigo de nivel servicio."))
    
    def srenvio_label(self, rate_id):
        url = werkzeug.urls.url_join(self.url, "labels")
        data = {
            "rate_id": rate_id,
            "label_format": "pdf"
        }
        ok, label = self._srenvio_request(url, data)
        if ok:
            label = label['data']
            url = label['attributes']['label_url']
            response = requests.get(url)
            if response.status_code == 200:
                label_base64 = base64.b64encode(response.content)
            else:
                label_base64 = None
            label['attributes'].update({ 'label_base64': label_base64})
            return label
        
        raise ValidationError(_("Fallo al generar la Guia, intente de nuevo por favor. \n %s" % label))
        
    def cancel_label(self, tracking_number, reason):
        url = werkzeug.urls.url_join(self.url, "cancel_label_requests")
        data = {
            "tracking_number": tracking_number,
            "reason": reason
        }
        ok, cancel_label = self._srenvio_request(url, data)
        if ok: 
            return cancel_label['data']
        raise ValidationError(_("Fallo al cancelar la guia, intente de nuevo por favor. \n %s" % cancel_label))
    
        # 
    
    def srenvio_cal_package(self, order):
        max_weight = self._srenvio_convert_weight(
            self.carrier.srenvio_default_packaging_id.max_weight, 
            self.carrier.srenvio_package_weight_unit)
        price = 0.0
        est_weight_value = sum([(line.product_id.weight * line.product_uom_qty) for line in order.order_line]) or 0.0
        weight = self._srenvio_convert_weight(est_weight_value, 
                                                    self.carrier.srenvio_package_weight_unit)
        package  = {
            'package_width': self.carrier.srenvio_default_packaging_id.width,
            'package_length': self.carrier.srenvio_default_packaging_id.length,
            'package_height': self.carrier.srenvio_default_packaging_id.height,
            
        }
        if max_weight and weight > max_weight:
            total_package = int(weight / max_weight)
            last_package_weight = weight % max_weight
            for sequence in range(1, total_package + 1):
                pass
            if last_package_weight:
                total_package = total_package + 1
            package.update({'weight':weight,'total_package':total_package })
        else:
            package.update({'weight':weight,'total_package':1 })
        print(package)
        return package 
        
    def _srenvio_convert_weight(self, weight, unit='KG'):
        if unit == 'KG':
            return weight
            """return self.carrier.env.ref('uom.product_uom_kgm')._compute_quantity(
                weight, 
                self.carrier.env.ref('uom.product_uom_kgm'), 
                round=False)"""
        else:
            raise ValueError