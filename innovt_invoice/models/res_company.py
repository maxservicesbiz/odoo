# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _
from requests import request
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    fiscal_name = fields.Char(string=_("Fiscal name"))
    invoice_series = fields.Char(string=_("Invoice series"))
    voucher_series = fields.Char(string=_("Voucher series"))
    property_account_position_id = fields.Many2one(comodel_name='account.fiscal.position', string=_("Position fiscal"))

    file_key = fields.Binary(string=_("File .key"))
    file_cer = fields.Binary(string=_("File .cer"))
    password = fields.Char(string=_("Password"))
    # api_key = fields.Char(string=_("API key"))
    mode = fields.Boolean(string=_("Test mode"))

    @api.multi
    def sync_csd_files(self):
        rp = {'TestMode': self.test_mode}
        if self.vat:
            rp.update(dict(Rfc=self.vat))
        else:
            raise ValidationError(_("Is necessary catch RFC"))
        if self.file_cer:
            rp.update(dict(Certificate=str(self.file_cer)))
        else:
            raise ValidationError(_("Is necessary catch the file CSD .cer"))
        if self.file_key:
            rp.update(dict(PrivateKey=str(self.file_key)))
        else:
            raise ValidationError(_("Is necessary catch the file CSD .key"))
        if self.password:
            rp.update(dict(PrivateKeyPassword=self.password))
        else:
            raise ValidationError(_("Is necessary catch the CSD password "))

        rq = self.env['msc.base.http.build.request'].request(
            method='POST',
            path='/api/cfdi/v1/csd',
            payload=rp,
        )
        print(rq)

