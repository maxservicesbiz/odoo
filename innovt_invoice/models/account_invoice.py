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
        if inv_type in ['out_invoice', 'in_invoice']:
            document_type = 'I'
        elif inv_type in ['out_refund', 'in_refund']:
            document_type = 'E'
        return document_type or ''

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
                                     copy=False)
    version = fields.Char(string=_("Version"), default='3.3', readonly=True, store=True, copy=False)

    type_relationship_id = fields.Many2one(comodel_name='type.relationship', string=_("Type of relationship"))
    uuid_relationship = fields.Char(string=_("Uuid relationship"))

    doc_pdf_id = fields.Many2one(comodel_name='ir.attachment', copy=False)
    doc_xml_id = fields.Many2one(comodel_name='ir.attachment', copy=False)

    # certificate_number = fields.Char(string=_("Certificate number"))
    # origin_string = fields.Char(string=_("Origin string"))
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
            raise MissingError(_("This document it is stamped!"))
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
                # doc_pdf_id = self.env['ir.attachment'].create({
                #    'name': '{}.pdf'.format(self.uuid),
                #    'type': 'binary',
                #    'datas': xml,
                #    'minetype': 'application/pdf'
                # })
                ##self.doc_pdf_id = doc_pdf_id
                self.datetime_stamp = date_invoice
                self.message_post(body=_("Is stamped OK"), attachment_ids=[self.doc_xml_id.id])
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
            # "CfdiRelated": {
            #    "Uuid": '',
            #    "TypeRelationship": ''
            # },
            #
        }
        company = self.company_id
        if company.invoice_series or False:
            cfdi.update(dict(Serie=company.invoice_series))
        else:
            raise Exception(_("Is necessary catch Invoice Series."))
        if company.currency_id or False:
            cfdi.update(dict(Currency=company.currency_id.name))
        else:
            raise Exception(_("Is necessary define one currency at company."))
        if company.zip or False:
            cfdi.update(dict(ExpeditionPlace=company.zip))
        else:
            raise Exception(_("Is necessary catch company zip for Expedition Place"))
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
            raise Exception(_("Is necessary select one Payment form"))
        if self.payment_method_id or False:
            cfdi.update(dict(PaymentMethod=self.payment_method_id.code))
        else:
            raise Exception(_("Is necessary select one Payment method"))

        return cfdi

    def get_receiver(self):
        receiver = {}
        if self.partner_id.vat or False:
            receiver.update(dict(Rfc=self.partner_id.vat[2:]))
        else:
            raise Exception(_("Is necessary catch RFC customer"))
        if self.partner_id.name or False:
            receiver.update(dict(Name=self.partner_id.name))
        else:
            pass
        if self.cfdi_use_id or False:
            receiver.update(dict(CfdiUse=self.cfdi_use_id.code))
        else:
            raise Exception(_("Is necessary select Use CFDI"))

        if self.partner_id.fiscal_residence.code3:
            if self.partner_id.fiscal_residence.code == '':
                raise Exception(_("Is necessary add code country for fiscal residence."))
            if self.partner_id.fiscal_residence.code3 != 'MEX':
                receiver.update(dict(FiscalResidence=self.partner_id.fiscal_residence.code3))
                if self.partner.tax_identity_registration_number:
                    receiver.update(dict(TaxIdentityRegistrationNumber=self.partner_id.tax_identity_registration_number))
                else:
                    raise Exception(_("It is necessary to write tax identity registration number of partner"))
        return receiver

    def get_issuer(self):
        issuer = {}
        company = self.company_id
        if company.property_account_position_id.code or False:
            issuer.update(dict(FiscalRegime=company.property_account_position_id.code))
        else:
            raise Exception(_("Is necessary define Fiscal regime company"))
        if company.fiscal_name or False:
            issuer.update(dict(Name=company.fiscal_name))
        else:
            raise Exception(_("Is necessary define fiscal name company"))
        if company.vat or False:
            issuer.update(dict(Rfc=company.vat))
        else:
            raise Exception(_("Is necessary catch RFC company"))
        return issuer

    def get_items(self):
        items = []
        if len(self.invoice_line_ids):
            for line in self.invoice_line_ids:
                product = {}
                p = line.product_id
                if p.product_code_id:
                    product.update(dict(ProductCode=p.product_code_id.code))
                else:
                    raise Exception(_("Is necessary define product code {}".format(p.name)))
                if p.default_code:
                    product.update(dict(IdentificationNumber=p.default_code))
                else:
                    raise Exception(_("Is necessary define product internal code {}".format(p.name)))
                if line.name:
                    product.update(dict(Description=line.name))
                else:
                    raise Exception(_("Is necessary define product description"))
                if line.uom_id:
                    product.update(dict(Unit=line.uom_id.name))
                else:
                    raise Exception(_("Is necessary define product unit of measure"))
                if p.product_unit_id:
                    product.update(dict(UnitCode=p.product_unit_id.code))
                else:
                    raise Exception(_("Is necessary define product unit"))
                if line.price_unit:
                    product.update(dict(UnitPrice=line.price_unit))
                else:
                    raise Exception(_("Is necessary define product price unit"))
                if line.quantity:
                    product.update(dict(Quantity=line.quantity))
                else:
                    raise Exception(_("Is necessary define product quantity"))
                if line.price_subtotal:
                    product.update(dict(Subtotal=line.price_subtotal))
                else:
                    raise Exception(_("Is necessary define product price subtotal"))
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
                    raise Exception(_("Is necessary define taxes"))
                if line.price_total:
                    product.update(dict(Total=line.price_total))
                else:
                    raise Exception(_("Is necessary define product price total"))
                items.append(product)
        else:
            raise Exception(_("Invoice lines is required"))
        return items

    @api.multi
    def invoice_stamp_cancel(self):
        self.ensure_one()
        if self.datetime_stamp_cancelled:
            raise MissingError(_("This document it is cancelled!"))
        try:
            self.configure_innov()
            date_invoice = fields.Datetime.now()
            rq = innov.Cfdi.cancel(rfc_issuer=self.env.user.company_id.vat, uuid=self.uuid)
            if rq.get('Success'):
                self.datetime_stamp_cancelled = date_invoice
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
        print(doc)
        doc = json.loads(doc)
        return doc

    @api.model
    def get_qr(self, doc):
        rfc_issuer = doc.get('{http://www.sat.gob.mx/cfd/3}Emisor').get('Rfc')
        rfc_receiver = doc.get('{http://www.sat.gob.mx/cfd/3}Receptor').get('Rfc')
        stamp = doc.get('{http://www.sat.gob.mx/cfd/3}Complemento').get(
            '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
        url = "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?&id={}&re={}&rr={}&tt={}&fe={}".format(
            stamp.get('UUID'),
            rfc_issuer,
            rfc_receiver,
            doc.get('Total'),
            stamp.get('SelloCFD')[-8:]
        )
        return quote(url)

    @api.model
    def get_product_taxes(self, taxes):
        if not taxes:
            return ''
        tax_str = ''
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
                    tax_str += ', '.join(map(
                        lambda tax: tax.get('Impuesto') + ' ' + tax.get('TipoFactor') + ' % ' + str(
                            float(tax.get('TasaOCuota', 0)) * 100) + ' $ ' + tax.get('Importe'), tax_record_type_list))
        return tax_str

    @api.model
    def get_taxes(self, taxes):
        taxes_list = []
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
                        taxes_list.append(row)
        return taxes_list

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
