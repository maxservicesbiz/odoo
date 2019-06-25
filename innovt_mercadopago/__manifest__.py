# -*- coding: utf-8 -*-
{
    'name': "Mercadopago Payment Acquirer",
    'summary': """ Payment Acquirer: Mercadopago Implementation""",
    'author': "MAXS",
    'website': "https://maxs.biz",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['payment'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/payment_mercadopago_templates.xml',
        'views/payment_view.xml',
        'data/payment_acquired_mercadopago_data.xml',
        
        
    ],
    'installable': True,
}