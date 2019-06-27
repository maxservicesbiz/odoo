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

from odoo import models, fields, api
from odoo.addons.innovt_mercadopago.controllers.main import InnovtMercadopagoController
from werkzeug import urls
import logging


_logger = logging.getLogger(__name__)

class InnovtAcquirerMercadopago(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('mercadopago', 'Mercadopago')])
    
    mercadopago_client_id = fields.Char('Client ID', 
                                       required_if_provider='mercadopago', 
                                       groups='base.group_user')
    mercadopago_client_secret = fields.Char('Client Secret', 
                                       required_if_provider='mercadopago', 
                                       groups='base.group_user')
 
    @api.multi
    def mercadopago_form_generate_values(self, values):
        self.ensure_one()
        mercadopago_tx_values = dict(values)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        mercadopago_tx_values.update({
            
        
            'mp_url_success': urls.url_join(base_url, InnovtMercadopagoController._url_success),
            'mp_url_failure':urls.url_join(base_url, InnovtMercadopagoController._url_failure),
            'mp_url_pending': urls.url_join(base_url, InnovtMercadopagoController._url_pending),
            'mp_url_notify': urls.url_join(base_url, InnovtMercadopagoController._url_notify),
            
            'mp_environment': self.environment,
            'mp_acquirer_id': self.id,
            
            'mp_item_name': '%s: %s' % (self.company_id.name, values.get('reference')),
            'mp_item_number': values.get('reference'),
            'mp_amount': values.get('amount'),
            'mp_currency':  values.get('currency').name,
            
            # Ship
            'mp_ship_mp_address': values.get('partner_address'),
            'mp_ship_city': values.get('partner_city'),
            'mp_ship_country': values.get('partner_country') and values.get('partner_country').name or '',
            'mp_ship_email': values.get('partner_email'),
            'mp_ship_zip_code': values.get('partner_zip'),
            'mp_ship_first_name': values.get('partner_first_name'),
            'mp_ship_last_name': values.get('partner_last_name'),
            'mp_ship_phone': values.get('partner_phone'),
            'mp_ship_state': values.get('partner_state').code,
             # Billing 
            'mp_billing_address': values.get('billing_partner_address'),
            'mp_billing_city': values.get('billing_partner_city'),
            'mp_billing_country': values.get('billing_partner_country') and values.get('billing_partner_country').name or '',
            'mp_billing_email': values.get('billing_partner_email'),
            'mp_billing_zip_code': values.get('billing_partner_zip'),
            'mp_billing_first_name': values.get('billing_partner_first_name'),
            'mp_billing_last_name': values.get('billing_partner_last_name'),
            'mp_billing_phone': values.get('billing_partner_phone'),
            'mp_billing_state':  values.get('billing_partner_state').code,
        })
        return mercadopago_tx_values
    
    

class TxMercadopago(models.Model):
    _inherit = 'payment.transaction'

    mercadopago_tx_id = fields.Char('Mercadopago transaction ID')
    mercadopago_tx_type = fields.Char('Mercadopago transaction type')
    
    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _mercadopago_form_get_tx_from_data(self, data):
        reference, txn_id = data.get('external_reference'), data.get('preference_id')
        if not reference or not txn_id:
            error_msg = _('Mercadopago: received data with missing reference (%s) or txn_id (%s)') % (reference, txn_id)
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'Mercadopago: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]
        
    """
    @api.multi
    def _mercadopago_form_get_invalid_parameters(self, data):
        invalid_parameters = [] # ("param", "value"), "type data"

        return invalid_parameters
    """
    
    @api.multi
    def _mercadopago_form_validate(self, data):
        """
            called is excecute tx.form_feedback() ...
        """
        status = data.get('collection_status')
        _data = {}
        _data.update({'mercadopago_tx_type': data.get('payment_type', False)})
        if status in ['approved', 'processed']:
            _logger.info('Validated MercadoPago payment for tx %s: set as done' % (self.reference))
            _data.update(state='done', date_validate=data.get('payment_date', fields.datetime.now()))
            return self.write(_data)
        elif status in ['pending', 'in_process','in_mediation']:
            _logger.info('Received notification for MercadoPago payment %s: set as pending' % (self.reference))
            _data.update(state='pending', state_message=data.get('pending_reason', ''))
            return self.write(_data)
        elif status in ['cancelled','refunded','charged_back','rejected']:
            _logger.info('Received notification for MercadoPago payment %s: set as cancelled' % (self.reference))
            _data.update(state='cancel', state_message=data.get('cancel_reason', ''))
            return self.write(_data)
        else:
            error = 'Received unrecognized status for MercadoPago payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            _data.update(state='error', state_message=error)
            return self.write(_data)

    