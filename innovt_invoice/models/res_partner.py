# -*- coding: utf-8 -*-
# Copyright 2018 Yonn Xyz. All rights reserved.


from odoo import models, fields, api, _, exceptions
import logging

_logger = logging.getLogger(__name__)

try:
    import stdnum.mx as stdnum_vat
except ImportError:
    _logger.warning(
        'Python `stdnum` library not found, unable to call VIES service to detect address based on VAT number.')
    stdnum_vat = None


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fiscal_residence = fields.Many2one(comodel_name='res.country', string=_("Fiscal residence"))
    tax_identity_registration_number = fields.Char(string=_("Tax identity registration number"))
    cfdi_use_id = fields.Many2one(comodel_name='cfdi.use', string=_("Cfdi use"))

    @api.onchange('vat')
    def vies_vat_change(self):
        try:
            super(ResPartner, self).vies_vat_change()
        except Exception:
            pass
        if stdnum_vat is None:
            return {}
        for partner in self:
            if not partner.vat:
                return {}
            if stdnum_vat.rfc.is_valid(partner.vat):
                partner.vat = stdnum_vat.rfc.compact(partner.vat)
                pass  # Using SDK INNOV
            else:
                try:
                    stdnum_vat.rfc.validate(partner.vat)
                except Exception as e:
                    partner.vat = False
                    raise exceptions.MissingError(str(e))
