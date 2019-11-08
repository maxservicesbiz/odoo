# -*- coding: utf-8 -*-
# Copyright 2019 Maxs Biz. All rights reserved.

from odoo import models, fields, api, _
import datetime
import base64

class InnovtDeclaraSAT(models.Model):
    _name = 'innovt.declara_sat'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'display_name'

    @api.model      
    def _get_current_month_of_year(self):
        today = datetime.date.today() 
        vals = []
        for m in range(1, 13):
            date = datetime.date(today.year, m, 1)
            vals.append(( date.strftime("%Y-%m"),date.strftime("%Y %B") ))
        return vals

    month = fields.Selection(
        string=_("Mes"), 
        selection=_get_current_month_of_year, 
        default=datetime.date.today().strftime("%Y-%m"), 
        required=True,
        help=_("Seleccione el mes que se declarara ante el SAT."),
    )
    
    declared_date = fields.Datetime(string = _("Fecha de declaración"))
    
    state = fields.Selection(
        string=_("Estatus"), 
        selection=[
            ('draft', _("Borrador")),
            ('diot', _("DIOT")),
            ('acknowledgment_receipt', _("Acuse de Recibo")),
            ('payment_format', _("Formato de Pago")),
            ('payment_ticket', _("Comprobante de Pago")),
            ('declared',_("Declarado")),
        ],
        default='draft',
        track_visibility='onchange',
        )
    
    
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name", store=True)    
    
    # Payment data    
    payment_date = fields.Datetime(string=_("Fecha de vencimiento de pago"))
    payment_amount = fields.Float(string=_("Monto de pago"))
    
    # Files
    fdiot_name = fields.Char(string="File Name")
    fdiot = fields.Binary(string=_("DIOT"))
    
    facknowledgment_receipt_name = fields.Char(string="File Name")
    facknowledgment_receipt = fields.Binary(string=_("Acuse de Recibo"))
    
    fpayment_format_name = fields.Char(string="File Name")
    fpayment_format = fields.Binary(string=_("Formato de pago"))
    
    fpayment_ticket_name = fields.Char(string="File Name")
    fpayment_ticket = fields.Binary(string=_("Comprobante de pago"))

    company_id = fields.Many2one('res.company', string='Compañia', required=True,
     default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    
    
    
    @api.multi
    @api.depends('month')
    def _compute_display_name(self):
        for row in self:
            date = datetime.datetime.strptime(row.month, "%Y-%m")
            row.display_name = date.strftime("%Y %B")

    @api.multi
    def action_diot(self):
        self.ensure_one()
        self.state = 'diot'
        
    @api.multi
    def action_acknowledgment_receipt(self):
        self.ensure_one()
        self.state = 'acknowledgment_receipt'
    
    @api.multi
    def action_payment_format(self):
        self.ensure_one()
        self.state = 'payment_format'
    
    @api.multi
    def action_payment_ticket(self):
        self.ensure_one()
        self.state = 'payment_ticket'

    @api.multi
    def action_repayment_format(self):
        self.ensure_one()
        self.state = 'payment_format'
        attachments = []
        if self.fpayment_format and self.fpayment_format_name:
            attachments=[(self.fpayment_format_name, base64.b64decode(self.fpayment_format))]
        body = """
            <p>
                <font style="font-size:14px">Se regenerara el formato de pago por fecha de vencimiento de pago.&nbsp;</font>
            </p>"""
        if self.payment_date and self.payment_amount:
            body += """
            <ul>
                <li>
                    <p>
                        <b style="font-weight:bold">Fecha de vencimiento de pago:</b>&nbsp; <font style="font-size:14px">{}</font> 
                    </p>
                </li>
                <li>
                    <p>
                        <b style="font-weight:bold">Monto de pago:</b> <font style="font-size:14px">${}</font><br>
                    </p>
                </li>
            </ul>
            """.format(fields.Datetime.context_timestamp(self,fields.Datetime.from_string(self.payment_date)), self.payment_amount)
        self.message_post(
            body=body,
            attachments = attachments
            )


        
    @api.multi
    def action_declared(self,):
        self.ensure_one()
        self.state = 'declared'
        self.declared_date = fields.datetime.now()
        
        