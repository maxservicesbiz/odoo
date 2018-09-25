# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.

from odoo.exceptions import MissingError
from odoo import models, fields, api, _
import uuid
import innov
from urllib.parse import quote
import base64
from xmljson import yahoo
from xml.etree.ElementTree import fromstring
import json

DOCUMENT_TYPE = [
    ('I', _("Incoming")),
    ('E', _("Outgoing")),
    ('T', _("Transfer"))
]


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def _default_document_type(self):
        inv_type = self._context.get('type', '')
        document_type = ''
        if inv_type in ['out_invoice']:
            document_type = 'I'
        elif inv_type in ['out_refund']:
            document_type = 'E'
        return document_type

    uuid = fields.Char(string=_("Uuid"), readonly=True, copy=False)

    payment_form_id = fields.Many2one(comodel_name='payment.form', string=_("Payment form"))
    payment_method_id = fields.Many2one(comodel_name='payment.method', string=_("Payment method"))
    cfdi_use_id = fields.Many2one(comodel_name='cfdi.use', string=_("Cfdi use"))

    datetime_stamp = fields.Datetime(string=_("Datetime stamp"), readonly=True, copy=False)
    datetime_stamp_cancelled = fields.Datetime(string=_("Datetime stamp cancelled"), readonly=True, copy=False)

    state_invoice = fields.Selection(
        selection=[('signed', _("Signed")), ('cancelled', _("Cancelled"))],
        string=_("State invoice"), readonly=True, copy=False)
    # Is replaced by document_type type selection
    # type_document_id = fields.Many2one(comodel_name='type.document', string=_("Type document"))
    document_type = fields.Selection(selection=DOCUMENT_TYPE, default=_default_document_type, readonly=True, store=True,
                                     copy=False, string=_("Document type"))
    version = fields.Char(string=_("Version"), default='3.3', readonly=True, store=True, copy=False)

    type_relationship_id = fields.Many2one(comodel_name='type.relationship', string=_("Type of relationship"),
                                           copy=False)
    uuid_relationship = fields.Char(string=_("Uuid relationship"), copy=False)

    doc_pdf_id = fields.Many2one(comodel_name='ir.attachment', copy=False)
    doc_xml_id = fields.Many2one(comodel_name='ir.attachment', copy=False)

    chain_tfd = fields.Text(string=_("Original chain tdf"))

    # chian_cfid = fields.Text(string=_("Original chain cfdi"))

    # digital_stamp = fields.Char(string=_("Digital stamp"))
    # sat_stamp = fields.Char(string=_("Sat stamp"))
    # currency_rate_alter = fields.Float(_("Currency rate alter"))
    # amount_total_text = fields.Char(string=_("Amount total text"))

    @api.model
    def configure_innov(self):
        innov.configure(
            {
                'mode': 'sandbox' if self.company_id.mode else 'live',
                'client_id': self.company_id.client_id,
                'client_secret': self.company_id.client_secret
            }
        )

    @api.multi
    def invoice_stamp(self):
        self.ensure_one()
        if self.datetime_stamp:
            raise MissingError(_("This document has already been stamped!"))
        try:
            self.configure_innov()
            date_invoice = fields.Datetime.now()
            cfdi = self.get_cfdi()
            cfdi.update({"Date": fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self, fields.Datetime.from_string(date_invoice)))})
            receiver = self.get_receiver()
            cfdi.update(dict(Receiver=receiver))
            issuer = self.get_issuer()
            cfdi.update(dict(Issuer=issuer))
            items = self.get_items()
            cfdi.update(dict(Items=items))
            cfdi_stamped = innov.Cfdi.stamp(data=cfdi)
            if cfdi_stamped.get('Success'):
                self.uuid = cfdi_stamped.get('Payload').get('Uuid')
                self.state_invoice = 'signed'
                xml = cfdi_stamped.get('Payload').get('ContentXml')
                self.doc_xml_id = self.env['ir.attachment'].create({
                    'name': '{}.xml'.format(self.uuid),
                    'type': 'binary',
                    # 'datas': base64.encodestring(pdf),
                    'datas': xml,
                    # 'res_model': 'account.invoice',
                    # 'res_id': self.id,
                    'mimetype': 'application/xml'
                })
                self.datetime_stamp = date_invoice
                self.message_post(body=_("This document was stamped correctly."), attachment_ids=[self.doc_xml_id.id])
            else:
                raise MissingError(cfdi_stamped.get('Message'))
        except Exception as e:
            raise MissingError(str(e))

    def get_cfdi(self):
        folio = self.number  # str(self.sequence_number_next_prefix) + str(self.sequence_number_next)
        cfdi = {
            "Folio": ''.join([n for n in folio if n.isdigit()]),
            "Rate": 1.0,
            "Receiver": False,
            "Issuer": False,
            "Items": False,
            # "Confirmation": ''
        }
        company = self.company_id
        if company.invoice_series or False:
            cfdi.update(dict(Serie=company.invoice_series))
        else:
            raise Exception(_("It's necessary to write the series of the invoice."))
        if company.currency_id or False:
            cfdi.update(dict(Currency=company.currency_id.name))
        else:
            raise Exception(_("It's necessary to define the currency of the company."))
        if company.zip or False:
            cfdi.update(dict(ExpeditionPlace=company.zip))
        else:
            raise Exception(_("Is necessary to write the zip of the company for Expedition Place"))
        if self.payment_term_id or False:
            cfdi.update(dict(PaymentConditions=self.payment_term_id.name))
        else:
            pass
        if self.document_type or False:
            cfdi.update(dict(CfdiType=self.document_type))
        else:
            pass
        if self.payment_form_id or False:
            cfdi.update(dict(PaymentForm=self.payment_form_id.code))
        else:
            raise Exception(_("It's mandatory select a Payment form"))
        if self.payment_method_id or False:
            cfdi.update(dict(PaymentMethod=self.payment_method_id.code))
        else:
            raise Exception(_("It's mandatory select a Payment method"))

        if self.uuid_relationship and self.type_relationship_id:
            cfdi.update(dict(CfdiRelated=dict(
                Uuid=self.uuid_relationship,
                TypeRelationship=self.type_relationship_id.code
            )))
        return cfdi

    def get_receiver(self):
        receiver = {}
        if self.partner_id.vat or False:
            receiver.update(dict(Rfc=self.partner_id.vat[2:]))
        else:
            raise Exception(_("The customer's RFC has not been captured."))
        if self.partner_id.name or False:
            receiver.update(dict(Name=self.partner_id.name))
        else:
            pass
        if self.cfdi_use_id or False:
            receiver.update(dict(CfdiUse=self.cfdi_use_id.code))
        else:
            raise Exception(_("It's mandatory select Use CFDI"))

        if self.partner_id.fiscal_residence.code3:
            if self.partner_id.fiscal_residence.code == '':
                raise Exception(_("It's necessary add code country for fiscal residence."))
            if self.partner_id.fiscal_residence.code3 != 'MEX':
                receiver.update(dict(FiscalResidence=self.partner_id.fiscal_residence.code3))
                if self.partner.tax_identity_registration_number:
                    receiver.update(
                        dict(TaxIdentityRegistrationNumber=self.partner_id.tax_identity_registration_number))
                else:
                    raise Exception(_("It's necessary to write tax identity registration number of customer"))
        return receiver

    def get_issuer(self):
        issuer = {}
        company = self.company_id
        if company.property_account_position_id.code or False:
            issuer.update(dict(FiscalRegime=company.property_account_position_id.code))
        else:
            raise Exception(_("The company has not been defined its Fiscal regime"))
        if company.fiscal_name or False:
            issuer.update(dict(Name=company.fiscal_name))
        else:
            raise Exception(_("The fiscal name of the company, please write."))
        if company.vat or False:
            issuer.update(dict(Rfc=company.vat))
        else:
            raise Exception(_("The company's RFC has not been captured."))
        return issuer

    def get_items(self):
        items = []
        if len(self.invoice_line_ids):
            for line in self.invoice_line_ids:
                product = {}
                p = line.product_id
                if p.product_code_id:
                    product_code = p.product_code_id.code
                    if self.document_type == 'E':
                        product_code = '84111506'
                    product.update(dict(ProductCode=product_code))
                else:
                    raise Exception(_("The product code is not defined. Please configure (%s)" % p.name))
                if p.default_code:
                    product.update(dict(IdentificationNumber=p.default_code))
                else:
                    raise Exception(_("Generate the product internal code (SKU) %s " % p.name))
                if line.name:
                    product.update(dict(Description=line.name))
                else:
                    raise Exception(_("Write the product description"))
                if line.uom_id:
                    product.update(dict(Unit=line.uom_id.name))
                else:
                    raise Exception(_("The  unit of measure to the product is not defined."))
                if p.product_unit_id:
                    unit_code = p.product_unit_id.code
                    if self.document_type == 'E':
                        unit_code = 'ACT'
                    product.update(dict(UnitCode=unit_code))
                else:
                    raise Exception(_("The  unit of measure to the product SAT is not defined."))
                if line.price_unit:
                    product.update(dict(UnitPrice=line.price_unit))
                else:
                    raise Exception(_("The price unit to the product it has to be greater zero"))
                if line.quantity:
                    product.update(dict(Quantity=line.quantity))
                else:
                    raise Exception(_("The product quantity it has to be greater zero"))
                if line.price_subtotal:
                    product.update(dict(Subtotal=line.price_subtotal))
                else:
                    raise Exception(_("The price subtotal of the product it has to be greater zero."))
                # if line.discount:
                product.update(dict(Discount=line.discount))
                # else:
                #    raise Exception(_("Is necessary define product price subtotal"))
                if line.invoice_line_tax_ids:
                    taxes = []
                    for tax in line.invoice_line_tax_ids:
                        if not tax.type_tax_id:
                            raise Exception(_("Define type tax IVA, ISR ..."))
                        if not tax.type_factor_id:
                            raise Exception(_("Define type factor TASA, CUOTA .."))
                        amount = tax.amount / 100
                        taxes.append({
                            "Total": line.price_subtotal * amount,
                            "Name": tax.type_tax_id.name,
                            "Code": tax.type_tax_id.code,
                            "Base": line.price_subtotal,
                            "Rate": amount,
                            "IsRetention": False,
                            "Type": tax.type_factor_id.code
                        })
                        product.update(dict(Taxes=taxes))
                else:
                    raise Exception(_("Define taxes of the product."))
                if line.price_total:
                    product.update(dict(Total=line.price_total))
                else:
                    raise Exception(_("The price total of the product it has to be greater zero."))
                items.append(product)
        else:
            raise Exception(_("Invoice lines is required"))
        return items

    @api.multi
    def invoice_stamp_cancel(self):
        self.ensure_one()
        if self.datetime_stamp_cancelled:
            raise MissingError(_("This document was cancelled correctly!"))
        try:
            self.configure_innov()
            date_invoice = fields.Datetime.now()
            rq = innov.Cfdi.cancel(rfc_issuer=self.env.user.company_id.vat, uuid=self.uuid)
            if rq.get('Success'):
                self.datetime_stamp_cancelled = date_invoice
                self.state_invoice = 'cancelled'
            else:
                raise MissingError(rq.get('Message'))
        except Exception as e:
            raise MissingError(str(e))

    @api.model
    def _get_report_cfdi_name(self):
        return str(self.uuid)

    @api.multi
    def invoice_cfdi2pdf(self):
        self.ensure_one()
        doc, doc_type = self.env.ref('innovt_invoice.templ_it_innovt_invoice_cfdi_report').render_qweb_pdf(self.ids)
        doc_pdf_id = self.env['ir.attachment'].create({
            'name': '{}.pdf'.format(self.uuid),
            'type': 'binary',
            'datas': base64.encodebytes(doc),
            'mimetype': 'application/html'
        })
        self.message_post(body=_("Pdf Ok"), attachment_ids=[doc_pdf_id.id])

    @api.model
    def get_xml(self, xmldata64=None):
        self.ensure_one()
        if not xmldata64:
            xmldata64 = self.doc_xml_id.datas
        if not xmldata64:
            raise MissingError(_("Not found Xml Data64"))
        xml2decode = base64.standard_b64decode(xmldata64)
        xml2json = yahoo.data(fromstring(xml2decode.decode('utf-8')))
        doc = xml2json.get('{http://www.sat.gob.mx/cfd/3}Comprobante')
        doc = json.dumps(doc)
        doc = json.loads(doc)
        return doc

    @api.model
    def get_url_qr(self, doc):
        data = self.get_params_cfdi_validate(doc=doc)
        url = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id={}&re={}&rr={}&tt={}&fe={}".format(
            data.get('uuid'), data.get('rfc-issuer'), data.get('rfc-receiver'), data.get('amount'),
            data.get('stamp-cfd')[-8:]
        )
        return quote(url)

    @api.model
    def get_product_taxes(self, taxes):
        if not taxes:
            return []
        list_taxes = []
        for tax_type_key in taxes.keys():
            tax_list = []
            tax_dict_or_list = taxes.get(tax_type_key)
            if isinstance(tax_dict_or_list, dict):
                tax_list.append(tax_dict_or_list)
            elif isinstance(tax_dict_or_list, list):
                tax_list = tax_dict_or_list
            for tax_row in tax_list:
                for tax_key in tax_row.keys():
                    tax_record_type = tax_row.get(tax_key)
                    tax_record_type_list = []
                    if isinstance(tax_record_type, dict):
                        tax_record_type_list.append(tax_record_type)
                    elif isinstance(tax_record_type, list):
                        tax_record_type_list = tax_record_type
                    for tax in tax_record_type_list:
                        tax_str = tax.get('Impuesto') + ' ' + str(float(tax.get('TasaOCuota', 0)) * 100) + ' % ' \
                                  + tax.get('TipoFactor') + ' $ ' + tax.get('Importe')
                        list_taxes.append(tax_str)
        return list_taxes

    @api.model
    def get_taxes(self, taxes):
        taxes_retencion = []
        taxes_traslados = []
        for taxes_key in taxes:
            tax_type = taxes.get(taxes_key)
            if isinstance(tax_type, dict):
                for tax_type_key in tax_type.keys():
                    sign = 1
                    if 'Retencion' in tax_type_key:
                        sign = -1
                    tax_type_records = tax_type.get(tax_type_key)
                    tax_type_record_list = []
                    if isinstance(tax_type_records, dict):
                        tax_type_record_list.append(tax_type_records)
                    elif isinstance(tax_type_records, list):
                        tax_type_record_list = tax_type_records
                    for row in tax_type_record_list:
                        row.update({'Importe': (float(row.get('Importe')) * sign)})
                        label = self.get_invoice_taxes(row.get('Impuesto'), row.get('Importe'))
                        row.update({'Etiqueta': label})
                        if 'Retencion' in tax_type_key:
                            taxes_retencion.append(row)
                        elif 'Traslado' in tax_type_key:
                            taxes_traslados.append(row)
        return taxes_traslados + taxes_retencion

    @api.model
    def get_products(self, products):
        products_list = []
        for products_key in products.keys():
            product = products.get(products_key)
            if isinstance(product, dict):
                products_list.append(product)
            elif isinstance(product, list):
                products_list = product
        return products_list

    @api.model
    def get_invoice_taxes(self, tax, amount):
        for row in self.tax_line_ids:
            if row.amount == amount:
                return row.name
        return False

    # Ncc / out_refund
    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        result = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice=date_invoice, date=date,
                                                             description=description, journal_id=journal_id)
        if self.state_invoice == 'signed' and isinstance(result, dict):
            result.update(dict(
                payment_form_id=self.payment_form_id.id,
                payment_method_id=self.payment_method_id.id,
                cfdi_use_id=self.env['cfdi.use'].search([('code', '=', 'G02')], limit=1).id or False,
                uuid_relationship=self.uuid,
                type_relationship_id=self.env['type.relationship'].search([('code', '=', '01')], limit=1).id or False,
                document_type='E'
            ))
        return result

    @api.model
    def get_chain_tfd(self):
        if not self.chain_tfd:
            self.configure_innov()
            data = {'ContentXml': self.doc_xml_id.datas.decode('utf-8')}
            result = innov.Cfdi.chain_tfd(data=data)
            print(result)
            if result.get('Success'):
                self.chain_tfd = result.get('Payload').get('ChainTfd')
        return self.chain_tfd

    @api.model
    def get_url_validate_uuid(self, doc):
        data = self.get_params_cfdi_validate(doc=doc)
        url = "https://innov.biz/cfdi-validate-uuid?uuid={}&rfc_issuer={}&rfc_receiver={}&amount={}".format(
            data.get('uuid'), data.get('rfc-issuer'), data.get('rfc-receiver'), data.get('amount')
        )
        return url

    @api.model
    def get_params_cfdi_validate(self, doc):
        stamp = doc.get('{http://www.sat.gob.mx/cfd/3}Complemento').get(
            '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
        return {
            'rfc-issuer': doc.get('{http://www.sat.gob.mx/cfd/3}Emisor').get('Rfc'),
            'rfc-receiver': doc.get('{http://www.sat.gob.mx/cfd/3}Receptor').get('Rfc'),
            'uuid': stamp.get('UUID'),
            'amount': doc.get('Total'),
            'stamp-cfd': stamp.get('SelloCFD')
        }
