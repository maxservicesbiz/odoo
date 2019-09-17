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
        selection=[('draft', _("Borrador")),('declared',_("Declarado"))],
        default='draft',
        tracking_visibility='onchange',
        )
    # Files
    declaration_request_fname = fields.Char(string="File Name")
    
    declaration_request = fields.Binary(string=_("Solicitud"))
    
    display_name = fields.Char(string=_("Display name"), compute="_compute_display_name", store=True)    
    
    @api.multi
    @api.depends('month')
    def _compute_display_name(self):
        for row in self:
            date = datetime.datetime.strptime(row.month, "%Y-%m")
            row.display_name = date.strftime("%Y %B")


    @api.multi
    def action_declared(self,):
        self.ensure_one()
        self.state = 'declared'
        self.declared_date = fields.datetime.now()
        
        