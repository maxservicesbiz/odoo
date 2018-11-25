# -*- coding: utf-8 -*-
# © Yonn, Xyz. All rights reserved.

from odoo import models, fields, api, _, exceptions
import innov
import base64

DOCUMENT_TYPE = [
    ('P', _("Payment")),
]


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    user_id = fields.Many2one('res.users', string='Salesperson', readonly=True,
                              default=lambda self: self.env.user, copy=False)
    payment_form_id = fields.Many2one(comodel_name='payment.form', string=_("Payment form"))
    payment_form_code = fields.Char(string=_("Payment form"), related='payment_form_id.code')
    document_type = fields.Selection(selection=DOCUMENT_TYPE, default='P', readonly=True, store=True,
                                     copy=False, string=_("Document type"))
    #outstanding_balance = fields.Float(_("Outstanding balance"))
    #amount_payable = fields.Float(_("Payable balance"))
    #remaining_balance = fields.Float(_("Remaining balance"))

    deposit_date = fields.Datetime(string=_("Deposit date"))
    stamp_date = fields.Datetime(string=_("Payment stamp date"))
    issuer_bank_id = fields.Many2one(comodel_name='res.bank', string=_('Issuer bank'))
    issuer_bank_account_id = fields.Many2one(comodel_name='res.partner.bank', string=_('Issuer bank account'))
    issuer_bank_vat = fields.Char(string=_('Issuer bank vat'), related='issuer_bank_id.vat')

    operation_number = fields.Char(_("Operation number"))
    receiver_bank_id = fields.Many2one(comodel_name='res.bank', string=_('Receiver bank'))
    receiver_bank_account_id = fields.Many2one(comodel_name='res.partner.bank', string=_('Receiver bank account'))
    receiver_bank_vat = fields.Char(string=_('Receiver bank vat'), related='receiver_bank_id.vat')

    state_payment = fields.Selection(selection=[('signed', _("Signed")), ('cancelled', _("Cancelled"))],
                                     string=_("State Payment"), readonly=True, copy=False)
    uuid = fields.Char(string=_("Uuid"), readonly=True)
    confirmation = fields.Char(string=_("Confirmation"))
    version = fields.Char(string=_("Version"), default='3.3', readonly=True, store=True, copy=False)

    type_relationship_id = fields.Many2one(comodel_name='type.relationship', string=_("Type of relationship"),
                                           copy=False)
    uuid_relationship = fields.Char(string=_("Uuid relationship"), copy=False)

    doc_pdf_id = fields.Many2one(comodel_name='ir.attachment', copy=False)
    doc_xml_id = fields.Many2one(comodel_name='ir.attachment', copy=False)

    chain_tfd = fields.Text(string=_("Original chain tdf"))

    @api.model
    def configure_innov_biz(self):
        innov.configure(self.env['res.config.settings'].sudo().get_innov_settings_api())

    @api.multi
    def payment_stamp(self):
        self.ensure_one()
        if self.state_payment == 'signed':
            raise exceptions.ValidationError(_("This document has already been stamped!"))
        else:
            try:
                self.configure_innov_biz()
                self.stamp_date = fields.Datetime.now()
                date = fields.Datetime.to_string(
                    fields.Datetime.context_timestamp(
                        self, fields.Datetime.from_string(self.stamp_date)
                    )
                )
                payment = self.get_cfdi()
                payment.update({"Date": date})
                payment.update(dict(Receiver=self.get_receiver()))
                payment.update(dict(Issuer=self.get_issuer()))
                payment.update(dict(Items=self.get_items()))
                payment.update(dict(ItemPayments=self.get_item_payments()))
                if self.uuid_relationship and self.type_relationship_id:
                    payment.update(dict(CfdiRelated=dict(
                        Uuid=self.uuid_relationship,
                        TypeRelationship=self.type_relationship_id.code
                    )))
                cfdi_stamped = innov.CfdiPayment.stamp(data=payment)
                if cfdi_stamped.get('Success'):
                    self.uuid = cfdi_stamped.get('Payload').get('Uuid')
                    self.state_payment = 'signed'
                    xml = cfdi_stamped.get('Payload').get('ContentXml')
                    self.doc_xml_id = self.env['ir.attachment'].create({
                        'name': '{}.xml'.format(self.uuid),
                        'datas_fname': '{}.pdf'.format(self.uuid),
                        'type': 'binary',
                        'datas': xml,
                        'mimetype': 'application/xml'
                    })
                    self.message_post(body=_("This document was stamped correctly."),
                                      attachment_ids=[self.doc_xml_id.id])
                else:
                    raise exceptions.MissingError(cfdi_stamped.get('Message'))
            except Exception as e:
                raise exceptions.MissingError(str(e))

    @api.model
    def get_cfdi(self):
        company = self.company_id
        cfdi = {
            'Folio': ''.join([n for n in self.name if n.isdigit()]),
            'Currency': 'XXX',
            'CfdiType': 'P',
        }
        if company.payment_series:
            cfdi.update(dict(Serie=company.payment_series))
        else:
            raise exceptions.ValidationError(
                _("The payment series is not captured in the company configuration, capture to continue."))
        if company.zip:
            cfdi.update(dict(ExpeditionPlace=company.zip))
        else:
            raise exceptions.ValidationError(
                _("The postal code of the place of expedition was not captured, capture to continue."))
        return cfdi

    @api.model
    def get_receiver(self):
        receiver = {
            'Name': self.partner_id.name,
            'CfdiUse': 'P01'
        }
        if self.partner_id.vat:
            receiver.update(dict(Rfc=self.partner_id.vat[2:]))
        else:
            raise exceptions.ValidationError(_("The RFC customer is not registered, please register for continue."))
        return receiver

    @api.model
    def get_issuer(self):
        issuer = {}
        company = self.company_id
        if company.property_account_position_id.code or False:
            issuer.update(dict(FiscalRegime=company.property_account_position_id.code))
        else:
            raise exceptions.ValidationError(_("The company has not defined the fiscal regime"))
        if company.fiscal_name:
            issuer.update(dict(Name=company.fiscal_name))
        else:
            raise exceptions.ValidationError(
                _("The fiscal name of the company has not been captured, please write to continue."))
        if company.vat:
            issuer.update(dict(Rfc=company.vat))
        else:
            raise exceptions.ValidationError(_("The RFC company is not registered, please register for continue"))
        return issuer

    @api.model
    def get_items(self):
        return [
            {
                'ProductCode': '84111506',
                'Description': 'Pago',
                'UnitCode': 'ACT',
                'UnitPrice': 0,
                'Quantity': 1,
                'Subtotal': 0,
                'Total': 0
            }
        ]

    @api.model
    def get_item_payments(self):
        item_payment = {
            'Currency': self.currency_id.name,
            'RelatedDocuments': self._get_related_documents()
        }
        total = 0
        for rd in item_payment.get('RelatedDocuments'):
            total += rd.get('AmountPaid')
        item_payment.update(dict(Total=total or self.amount))

        if self.deposit_date:
            date = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(
                    self, fields.Datetime.from_string(self.deposit_date)
                )
            )
            item_payment.update(dict(PaymentDate=date))
        else:
            raise exceptions.ValidationError(_("Please capture payment deposit date."))

        if self.payment_form_id.code:
            item_payment.update(dict(PaymentForm=self.payment_form_id.code))
        else:
            raise exceptions.ValidationError(_("Select a payment form."))

        if self.operation_number:
            item_payment.update(dict(OperationNumber=self.operation_number))
        else:
            raise exceptions.ValidationError(_("Capture the transaction number as a payment reference."))

        if self.issuer_bank_id:
            item_payment.update(dict(
                IssuerBankRfc=self.issuer_bank_vat,
                IssuerBankAccount=self.issuer_bank_account_id.acc_number,
                IssuerBankName=self.issuer_bank_id.name
            ))
        if self.receiver_bank_id:
            item_payment.update(dict(
                ReceiverBankRfc=self.receiver_bank_vat,
                ReceiverBankAccount=self.receiver_bank_account_id.acc_number,
                ReceiverBankName=self.receiver_bank_id.name
            ))

        return [item_payment]

    @api.model
    def _get_related_documents(self):
        related_documents = []
        for invoice_id in self.invoice_ids:
            related_document = {
                'Uuid': invoice_id.uuid,
                'Serie': invoice_id.company_id.invoice_series,
                'Folio': ''.join([n for n in invoice_id.number if n.isdigit()]),
                'Currency': invoice_id.currency_id.name,
                'PaymentMethod': 'PPD',
                'BiasNumber': len(invoice_id.payment_ids),
                'PreviousBalanceAmount': self.amount + invoice_id.residual,
                'AmountPaid': self.amount,
                'UnpaidBalanceAmount': invoice_id.residual

            }
            related_documents.append(related_document)
        return related_documents

    # Make to PDF
    @api.model
    def get_xml(self):
        return self.env['account.invoice'].sudo().get_xml(xmldata64=self.doc_xml_id.datas)

    @api.model
    def get_url_qr(self, doc):
        return self.env['account.invoice'].sudo().get_url_qr(doc=doc)

    @api.model
    def get_product_taxes(self, taxes):
        return self.env['account.invoice'].sudo().get_product_taxes(taxes=taxes)

    @api.model
    def get_taxes(self, taxes):
        return self.env['account.invoice'].sudo().get_taxes(taxes=taxes or [])

    @api.model
    def get_products(self, products):
        return self.env['account.invoice'].sudo().get_products(products=products)

    @api.model
    def get_invoice_taxes(self, tax, amount):
        return self.env['account.invoice'].sudo().get_invoice_taxes(tax=tax, amount=amount)

    @api.model
    def get_chain_tfd(self):
        if not self.chain_tfd:
            self.configure_innov_biz()
            data = {'ContentXml': self.doc_xml_id.datas.decode('utf-8')}
            result = innov.Cfdi.chain_tfd(data=data)
            if result.get('Success'):
                self.chain_tfd = result.get('Payload').get('ChainTfd')
        return self.chain_tfd

    @api.model
    def get_url_validate_uuid(self, doc):
        return self.env['account.invoice'].sudo().get_url_validate_uuid(doc=doc)

    @api.model
    def get_params_cfdi_validate(self, doc):
        return self.env['account.invoice'].sudo().get_params_cfdi_validate(doc=doc)

    @api.model
    def _get_report_cfdi_name(self):
        return str(self.uuid)

    @api.model
    def get_payments(self, doc):
        return doc.get('{http://www.sat.gob.mx/cfd/3}Complemento').get('{http://www.sat.gob.mx/Pagos}Pagos').get('{http://www.sat.gob.mx/Pagos}Pago')

    @api.model
    def get_related_documents(self, doc):
        related_documents = self.get_payments(doc=doc)
        related_documents = related_documents.get('{http://www.sat.gob.mx/Pagos}DoctoRelacionado')
        if isinstance(related_documents, dict):
            return [related_documents]
        return related_documents

    @api.multi
    def payment_cfdi2pdf(self):
        self.ensure_one()
        doc, doc_type = self.env.ref('innovt_payment.repo_it_innovt_payment_cfdi_report').render_qweb_pdf(self.ids)
        if not self.doc_pdf_id:
            doc_pdf_id = self.env['ir.attachment'].create({
                'name': '{}.pdf'.format(self.uuid),
                'datas_fname': '{}.pdf'.format(self.uuid),
                'type': 'binary',
                'datas': base64.encodebytes(doc),
                'mimetype': 'application/pdf'
            })
            self.doc_pdf_id = doc_pdf_id
        else:
            self.doc_pdf_id.datas = base64.encodebytes(doc)

    @api.multi
    def payment_print(self):
        if self.state_payment:
            return self.env.ref('innovt_payment.repo_it_innovt_payment_cfdi_report').report_action(self)

    @api.multi
    def action_payment_sent(self):
        template = self.env.ref('innovt_payment.email_template_cfdi_payment', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        self.payment_cfdi2pdf()
        ctx = dict(
                default_model='account.payment',
                default_res_id=self.id,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                default_composition_mode='comment',
                mark_invoice_as_sent=True,
                default_attachment_ids=[self.doc_xml_id.id, self.doc_pdf_id.id],
                #custom_layout="innovt_payment.mail_template_cfdi_payment_notification",
                force_email=True
            )
        return {
                'name': _('Compose Email'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form.id, 'form')],
                'view_id': compose_form.id,
                'target': 'new',
                'context': ctx,
            }