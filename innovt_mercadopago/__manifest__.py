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

{
    'name': "Mercadopago Payment Acquirer",
    'summary': """ Payment Acquirer: Mercadopago Implementation""",
    'author': "MAXS",
    'website': "https://maxs.biz",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['payment','innovt_client'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_mercadopago_templates.xml',
        'views/payment_view.xml',
        'data/payment_acquired_mercadopago_data.xml',
        
        
    ],
    'installable': True,
}