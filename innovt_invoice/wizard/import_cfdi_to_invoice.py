# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
import innov


class ImportCfdiToInvoice(models.TransientModel):
    _name = 'innovt_invoice.import_cfdi_to_invoice'

    create_products = fields.Boolean(string=_("Crear productos"))
    validate_uuid = fields.Boolean(string=_("Validar uuid SAT"))
    cfdi_xml = fields.Binary(string=_("XML"))
    cfdi_pdf = fields.Binary(string=_("PDF"))

    @api.multi
    def import_cfdi(self):
        try:
            invoice = self.env['account.invoice'].get_xml(self.cfdi_xml)
        except Exception as e:
            raise exceptions.MissingError(_("El archivo XML no tiene el formato CFDI 3.3"))
        invoice_id = self.create_invoice(invoice)
        return {
            'name': _('Invoice vendor'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(invoice_id.get_formview_id(), 'form')],
            'view_id': invoice_id.get_formview_id(),
            'target': 'main',
            'res_id': invoice_id.id,
            'context': {},
        }

    @api.model
    def create_invoice(self, doc):
        stamp = self.get_stamp(doc)

        data = {
            'reference': doc.get('Serie', '') + '-' + doc.get('Folio'),
            # 'partner_bank_id': 2,
            # 'payment_term_id': False,
            'invoice_line_ids': self.get_invoice_line(doc),
            # 'fiscal_position_id': False,
            # 'name': False,
            # 'tax_line_ids': [[0, 'virtual_207',
            #                  {'currency_id': 34, 'sequence': 1, 'account_analytic_id': False, 'manual': False,
            #                   'amount': -35.04, 'name': 'RET IVA FLETES 4%', 'account_id': 23, 'amount_rounding': 0,
            #                   'tax_id': 3}]],
            # 'account_id': 16,
            # 'journal_id': 2,
            # 'comment': False,
            # 'sequence_number_next': False,
            # 'user_id': 1,
            # 'currency_id': 34,
            'date_due': False,
            'company_id': self.get_receiver(doc).id,
            # 'move_name': False,
            # 'origin': False,
            'date_invoice': doc.get('Fecha')[0:10],
            'partner_id': self.get_issuer(doc).id,
            # 'date': False,
            'type': 'in_invoice',
            'uuid': stamp.get('uuid')
        }
        invoice_id = self.env['account.invoice'].create(data)
        attachment_ids = self.create_attachments(invoice_id)
        if len(attachment_ids):
            invoice_id.message_post(
                body=_("Documentos CFDI."),
                attachment_ids=[r.id for r in attachment_ids]
            )
        if self.validate_uuid:
            innov.configure(self.env['res.config.settings'].sudo().get_innov_api_settings())
            try:
                res = innov.Cfdi.validate_uuid([{
                    "Uuid": stamp.get('uuid'),
                    "Issuer": doc.get('{http://www.sat.gob.mx/cfd/3}Emisor').get('Rfc'),
                    "Receiver": doc.get('{http://www.sat.gob.mx/cfd/3}Receptor').get('Rfc'),
                    "Amount": float(doc.get('Total'))
                }])
                if res.get('Success'):
                    payload = res.get('Payload')
                    if len(payload):
                        body = ""
                        for pl in payload:
                            for item in pl:
                                body += """<li>{}: <span>{}</span></li>""".format(item, pl[item])
                        invoice_id.message_post(body=body)
                else:
                    raise Exception(res.get('Message'))
            except Exception as e:
                raise exceptions.MissingError(str(e))
        return invoice_id

    @api.model
    def get_stamp(self, doc):
        stamp = doc.get('{http://www.sat.gob.mx/cfd/3}Complemento', {}).get(
            '{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital', {})
        return {
            'uuid': stamp.get('UUID'),
        }

    @api.model
    def create_attachments(self, invoice_id):
        docs = []
        doc_xml_id = self.env['ir.attachment'].create({
            'name': '{}.xml'.format(invoice_id.uuid),
            'datas_fname': '{}.xml'.format(invoice_id.uuid),
            'type': 'binary',
            'res_model': 'account.invoice',
            'res_id': invoice_id.id,
            'datas': self.cfdi_xml,
            'mimetype': 'application/xml'
        })
        docs.append(doc_xml_id)
        if self.cfdi_pdf:
            doc_pdf_id = self.env['ir.attachment'].create({
                'name': '{}.pdf'.format(invoice_id.uuid),
                'datas_fname': '{}.pdf'.format(invoice_id.uuid),
                'type': 'binary',
                'res_model': 'account.invoice',
                'res_id': invoice_id.id,
                'datas': self.cfdi_pdf,
                'mimetype': 'application/pdf'
            })
            docs.append(doc_pdf_id)
        return docs

    @api.model
    def get_invoice_line(self, doc):
        products = self.get_products(doc)
        invoice_lines = []
        journal_id = self.env['account.invoice'].with_context(type='in_invoice')._default_journal().id
        account_id = self.env['account.invoice.line'].with_context(journal_id=journal_id,
                                                                   type='in_invoice')._default_account()

        for product in products:
            product_id = False
            if self.create_products:
                product_id = self.create_product(product).id or False
            invoice_lines.append([0, 'virtual_' + str(1), {
                # 'account_analytic_id': False,
                # 'uom_id': 1,
                'invoice_line_tax_ids': self.get_invoice_line_tax(product),
                'price_unit': product.get('ValorUnitario'),
                # 'discount': 0,
                # 'sequence': 10,
                'product_id': product_id,
                # 'analytic_tag_ids': [[6, False, []]],
                'name': str(product.get('Descripcion')).upper(),
                'account_id': account_id,
                'quantity': product.get('Cantidad')}])
        return invoice_lines

    @api.model
    def create_product(self, product):
        default_code = str(product.get('NoIdentificacion', '')).upper()
        name = str(product.get('Descripcion')).upper()
        product_id = self.env['product.product'].search([
            '|', ('default_code', '=', default_code), ('name', '=', name)
        ], limit=1)
        price = product.get('ValorUnitario', 0)
        if not len(product_id):
            product_id = self.env['product.product'].create({
                'default_code': default_code,
                'name': name,
                'purchase_ok': True,
                'sale_ok': False,
                'type': 'service',
                'standard_price': price,
                'lst_price': price,
                'product_unit_id': self.env['product.unit'].search(
                    [('code', '=', product.get('ClaveUnidad', ''))], limit=1).id or False,
                'product_code_id': self.env['product.code'].search(
                    [('code', '=', product.get('ClaveProdServ', ''))], limit=1).id or False
            })
        return product_id

    @api.model
    def get_invoice_line_tax(self, product):
        taxes = product.get('{http://www.sat.gob.mx/cfd/3}Impuestos', False)
        if not taxes:
            return []
        tax_traslados = taxes.get('{http://www.sat.gob.mx/cfd/3}Traslados', {}).get(
            '{http://www.sat.gob.mx/cfd/3}Traslado', {})
        if isinstance(tax_traslados, dict) and len(tax_traslados):
            tax_traslados = [tax_traslados]
        taxes_erp = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')])
        tax_list = []
        for tax in tax_traslados:
            tax_amount = round(float(tax.get('TasaOCuota', 0)) * 100, 2)
            for tax_erp in taxes_erp:
                tax_erp_amount = round(tax_erp.amount, 2)
                if tax_erp.type_tax_id.code == tax.get('Impuesto') \
                        and tax_erp.type_factor_id.code == tax.get('TipoFactor'):
                    if tax_amount == tax_erp_amount:
                        tax_list.append([6, False, [tax_erp.id]])
                        break
                elif tax_amount == tax_erp_amount:
                    tax_list.append([6, False, [tax_erp.id]])
                    break
                else:
                    """ Not found tax """
                    pass
        return tax_list

    @api.model
    def get_issuer(self, doc):
        issuer = doc.get('{http://www.sat.gob.mx/cfd/3}Emisor')
        partner_id = self.env['res.partner'].search([('supplier', '=', True), ('vat', '=', issuer.get('Rfc'))])
        if not len(partner_id):
            partner_id = self.env['res.partner'].create({
                'name': str(issuer.get('Nombre', '')).upper(),
                'vat': str(issuer.get('Rfc')).upper(),
                'supplier': True
            })
        return partner_id

    @api.model
    def get_receiver(self, doc):
        receiver = doc.get('{http://www.sat.gob.mx/cfd/3}Receptor')
        company_id = self.env['res.company'].search([('vat', '=', receiver.get('Rfc'))])
        if not len(company_id):
            company_id = self.env.user.company_id
        return company_id

    @api.model
    def get_products(self, doc):
        products_node = doc.get('{http://www.sat.gob.mx/cfd/3}Conceptos')
        products = self.env['account.invoice'].get_products(products_node)
        return products
