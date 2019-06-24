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

from odoo import models, fields, api, _
import logging
from odoo.exceptions import  ValidationError
from .srenvio_request import SrenvioProvider

_logger = logging.getLogger(__name__)


class ProviderSrenvio(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('srenvio', "SrEnvio")])

    srenvio_token = fields.Char(string="Token")
    srenvio_package_dimension_unit = fields.Selection([('CM', 'Centimeters')],
                                                  default='CM',
                                                  string='Package Dimension Unit')
    srenvio_package_weight_unit = fields.Selection([('KG', 'Kilograms')],
                                               default='KG',
                                               string="Package Weight Unit")
    srenvio_default_packaging_id = fields.Many2one('product.packaging', 
                                                   string="Default Package Type")
             
    def srenvio_rate_shipment(self, order):
        se = SrenvioProvider(self)
        provider = self._context.get('provider', order.srenvio_provider)
        service_level_code = self._context.get('service_level_code', order.srenvio_service_level_code)
        success = False
        price =  False
        error_message = "Provider and Service level code missing context."
        warning_message = False
        if provider and service_level_code:
            quotations = se.srenvio_quotations(order)
            error_message = _("Fallo al generar la cotización, intente de nuevo o cambie de paqueteria.")
            if len(quotations):
                error_message = "Provider and Service level code not fond in the quotations, Select other provider please."
                for quotation in quotations: 
                    if quotation['provider'] == provider and quotation['service_level_code'] == service_level_code:
                        price = quotation['total_pricing']
                        success =  True
                        error_message = False
                        order.srenvio_provider = provider
                        order.srenvio_service_level_code = service_level_code
                        break                    
        return {'success': success,
                'price': price,
                'error_message': error_message,
                'warning_message': warning_message}
       
    def srenvio_send_shipping(self, pickings):
        se = SrenvioProvider(self)
        res = []
        for picking in pickings:
            order = picking.sale_id
            company = order.company_id or picking.company_id or self.env.user.company_id
            shipping = se.srenvio_shipments(order)
            package = se.srenvio_cal_package(order)
            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id
            if order_currency.name == shipping['attributes']['currency_local']:
                carrier_price = float(shipping['attributes']['total_pricing'])
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', shipping['attributes']['currency_local'])], limit=1)
                carrier_price = quote_currency._convert(float(shipping['attributes']['total_pricing']), order_currency, company, order.date_order or fields.Date.today())
            picking.srenvio_shipping_id = int(shipping['shipping_id'])
            picking.srenvio_label_id = int(shipping['id'])
            label = se.srenvio_label(picking.srenvio_label_id)
            carrier_tracking_ref = label['attributes']['tracking_number']
            picking.srenvio_tracking_ref =  label['attributes']['tracking_url_provider']
            logmessage = """
            Guía generada en SrEnvio <br/>
            <ul class="o_mail_thread_message_tracking">
                <li>No. Paquetes: {}</li>
                <li>Código de rastreo: <span>{}</span></li>
                <li><a href='{}' target='_blank'>Link de rastreo ...</a></li>
                <li><a href='{}' target='_blank'>Descargar Guia ...</a></li>
            </ul>""".format(package.get('total_package'), carrier_tracking_ref,
                            picking.srenvio_tracking_ref,
                            label['attributes']['label_url'])
            if label['attributes']['label_base64']:
                attachment = [('LabelSrenvio-%s.pdf' % (carrier_tracking_ref), label['attributes']['label_base64'])]
            else:
                attachment = []
            picking.message_post(body=logmessage, attachments=attachment)
            shipping_data = {
                'exact_price': carrier_price,
                'tracking_number': carrier_tracking_ref
            }
            res = res + [shipping_data]
        return res

    def srenvio_get_tracking_link(self, picking):
        return picking.srenvio_tracking_ref

    def srenvio_cancel_shipment(self, picking):        
        reason =  _("Cliente cancelo la compra.")
        se = SrenvioProvider(self)
        clabel = se.cancel_label(picking.carrier_tracking_ref, reason)
        picking.write({'carrier_tracking_ref': '', 'carrier_price': 0.0})
        reason += "Estatus: " + clabel.get('attributes',{}).get('status', "")
        picking.message_post(body=reason)
        
    