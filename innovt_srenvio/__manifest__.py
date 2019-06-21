# -*- coding: utf-8 -*-
{
    'name': "Srenvio Shipping",

    'summary': """

        """,

    'author': "Max Solutions, Co",
    'website': "https://max-solutions.co",

    'category': 'Warehouse',
    'version': '0.1',

    'depends': ['delivery', 'mail','website_sale_delivery'],

    'data': [
        
        'views/sale_order_view.xml',
        'views/delivery_view.xml',
        'views/website_sale_srenvio_delivery_templates.xml',
        'data/delivery_srenvio_data.xml',
    ],
}