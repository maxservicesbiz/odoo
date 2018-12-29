# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _
import innov
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    fiscal_name = fields.Char(string=_("Fiscal name"))
    invoice_series = fields.Char(string=_("Invoice series"))
    # voucher_series = fields.Char(string=_("Voucher series"))
    property_account_position_id = fields.Many2one(comodel_name='account.fiscal.position', string=_("Position fiscal"))

    file_key = fields.Binary(string=_("File .key"))
    file_cer = fields.Binary(string=_("File .cer"))
    password = fields.Char(string=_("Password"))
    is_sync_csd = fields.Boolean(string=_("Is sync CSD's?"))

    @api.model
    def configure_innov_biz(self):
        innov.configure(self.env['res.config.settings'].sudo().get_innov_settings_api())

    @api.multi
    def sync_csd(self):
        rp = {
            'CompanyName': self.fiscal_name or self.name
        }

        if self.vat:
            rp.update(dict(Rfc=self.vat))
        else:
            raise ValidationError(_("Is necessary catch RFC"))
        if self.file_cer:
            rp.update(dict(Certificate=self.file_cer.decode('UTF-8')))
        else:
            raise ValidationError(_("Is necessary catch the file CSD .cer"))
        if self.file_key:
            rp.update(dict(PrivateKey=self.file_key.decode('UTF-8')))
        else:
            raise ValidationError(_("Is necessary catch the file CSD .key"))
        if self.password:
            rp.update(dict(PrivateKeyPassword=self.password))
        else:
            raise ValidationError(_("Is necessary catch the CSD password "))
        try:
            response = {}
            self.configure_innov_biz()
            if self.is_sync_csd:
                response = innov.CfdiCsd.update(data=rp)
            else:
                response = innov.CfdiCsd.create(data=rp)
            if response.get('Success', False):
                self.is_sync_csd = True
            else:
                raise Exception(response.get('Message', _('Error to request')))
        except Exception as e:
            raise ValidationError(str(e))
