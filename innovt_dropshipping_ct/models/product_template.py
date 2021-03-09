# -*- coding: utf-8 -*-
#   Copyright (C) 2019  MAXS
#   
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#   
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from odoo import models, fields, api, _
from .ct_mayorista_lib import CTMayoristaLib
import subprocess
import os
from odoo.tools.config import config
import json

class InnovtDropshippingProductTemplate(models.Model):
    _inherit = 'product.template'

    ct_features = fields.Html("CT Caracteristicas")
    ct_data_sheet = fields.Html("CT Ficha tecnica")


    @api.multi
    def action_ct_features_data_sheet(self ):
        ct =  self.env['innovt_dropshipping_ct_mayorista_sync']
        ct.with_context(products_published=self).cron_do_task_product_feature_and_data_sheet(force_update=True)


        
    
