# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.

from odoo.exceptions import MissingError
from odoo import models, fields, api, _
import random


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    way_pay_id = fields.Many2one(comodel_name='way.pay', string=_("Way to pay"))
    payment_method_id = fields.Many2one(comodel_name='payment.method', string=_("Payment method"))
    merchandise_use_id = fields.Many2one(comodel_name='merchandise.use', string=_("Merchandise use"))

    state_invoice = fields.Selection(
        selection=[('signed', _("Signed")), ('canceled', _("Canceled"))],
        string=_("State invoice"))
    type_document_id = fields.Many2one(comodel_name='type.document', string=_("Type document"))
    uuid = fields.Char(string=_("Uuid"))
    datetime_invoice = fields.Datetime(string=_("Amount Datetime invoice"))
    version = fields.Char(string=_("Version"))

    type_relationship_id = fields.Many2one(comodel_name='type.relationship', string=_("Type of relationship"))
    uuid_relationship = fields.Char(string=_("Uuid relationship"))

    doc_pdf = fields.Binary()
    doc_xml = fields.Binary()
    certificate_number = fields.Char(string=_("Certificate number"))
    origin_string = fields.Char(string=_("Origin string"))
    digital_stamp = fields.Char(string=_("Digital stamp"))
    sat_stamp = fields.Char(string=_("Sat stamp"))
    currency_rate_alter = fields.Float(_("Currency rate alter"))
    amount_total_text = fields.Char(string=_("Amount total text"))

    @api.multi
    def invoice_stamp(self):
        try:
            cfdi = self.get_cfdi()
            receiver = self.get_receiver()
            cfdi.update(dict(Receiver=receiver))
            issuer = self.get_issuer()
            cfdi.update(dict(Issuer=issuer))
            items = self.get_items()
            cfdi.update(dict(Items=items))
            cfdi.update(dict(TestMode=self.env.user.company_id.test_mode))
            print(cfdi)
            rq = self.env['msc.base.http.build.request'].request(
                method='POST',
                path='/api/cfdi/v1/stamp',
                payload=cfdi,
            )

            print(rq)
            import pdb;
            pdb.set_trace()
        except Exception as e:
            raise MissingError(str(e))

    def get_cfdi(self):
        self.ensure_one()
        cfdi = {
            "Folio": random.randint(1, 999999999),  # self.number,
            "Receiver": False,
            "Issuer": False,
            "Items": False
        }
        company = self.env.user.company_id
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
        if self.type_document_id or False:
            cfdi.update(dict(CfdiType=self.type_document_id.code))
        else:
            pass
        if self.way_pay_id or False:
            cfdi.update(dict(PaymentForm=self.way_pay_id.code))
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
        if self.merchandise_use_id or False:
            receiver.update(dict(CfdiUse=self.merchandise_use_id.code))
        else:
            raise Exception(_("Is necessary select Use CFDI"))
        return receiver

    def get_issuer(self):
        issuer = {}
        company = self.env.user.company_id
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
                            "Base": line.price_subtotal,
                            "Rate": amount,
                            "IsRetention": False,
                            "Factor": tax.type_factor_id.code
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
        cfdi = dict(
            Uuid=self.uuid,
            CfdiType=self.type_document_id.code,
            Rfc=self.env.user.company_id.vat
        )
        rq = self.env['msc.base.http.build.request'].request(
            method='DELETE',
            path='/api/cfdi/v1/stamp',
            payload=cfdi,
        )
        print(rq)
