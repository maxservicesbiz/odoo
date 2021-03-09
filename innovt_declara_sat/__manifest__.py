# -*- coding: utf-8 -*-
# Copyright 2019 Maxs Biz. All rights reserved.

{
    'name': "Innovt Declara SAT",
    'summary': """ Almacena los documentos de la declaracion mensual/anual en la nube.""",
    'author': "MAXS",
    'website': "https://maxs.biz",
    'category': 'Accounting',
    'version': '0.2',
    'depends': ['account_invoicing','innovt_client','mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/declara_sat_security.xml',
        'views/declara_sat_view.xml',
    ],
    'installable': True,
}