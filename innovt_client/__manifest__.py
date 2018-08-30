# -*- coding: utf-8 -*-
# © Yonn, Xyz. All rights reserved.
{
    'name': "Innov Client",

    'summary': """
        Controller Innov <--> Client, is mandatory install and 
        dangerous unintall, if is unistalled we are not
        resposability the futures problems or damage in the db.
        """,

    'author': "Yonn, Xyz",
    'website': "https://innov.biz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'saas',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_company.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}