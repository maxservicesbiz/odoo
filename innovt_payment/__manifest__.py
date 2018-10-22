{
    'name': "Innov Payment",

    'summary': """
        This module use guidelines or rules 
        issued by SAT, begin rules 1.0...
        """,

    'author': "Innov, Biz",
    'website': "https://innov.biz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Payment',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account_invoicing',
        'innovt_invoice'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/res_bank.xml',
        'views/account_payment.xml',
        'views/reports/cfdi.xml'
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
# -*- coding: utf-8 -*-
