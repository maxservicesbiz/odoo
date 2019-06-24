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
    'name': "Srenvio Shipping",

    'summary': """

        """,

    'author': "MAXS",
    'website': "https://www.maxs.biz",

    'category': 'Warehouse',
    'version': '0.1',

    'depends': ['innovt_client',
                'delivery',
                 'mail',
                 'website_sale_delivery'],

    'data': [
        
        'views/sale_order_view.xml',
        'views/delivery_view.xml',
        'views/website_sale_srenvio_delivery_templates.xml',
        'data/delivery_srenvio_data.xml',
    ],
}