# -*- coding: utf-8 -*-
# Copyright 2019 Maxs Biz. All rights reserved.

from odoo import models, fields, api, _
import datetime

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
            ('acknowledgment_receipt', _("A. Recibo")),
            ('payment_format', _("F. Pago")),
            ('payment_ticket', _("C. Pago")),
            ('declared',_("Declarado")),
        ],
        default='draft',
        track_visibility='onchange',
        )
    
    
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name", store=True)    
    
    # Payment data    
    payment_date = fields.Datetime(string=_("Fecha de pago"))
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
        self.message_post(body="Se regerara el formato de pago por fecha de vencimiento de pago.")


        
    @api.multi
    def action_declared(self,):
        self.ensure_one()
        self.state = 'declared'
        self.declared_date = fields.datetime.now()
        
        