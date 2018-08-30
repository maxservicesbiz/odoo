# -*- coding: utf-8 -*-
{
    'name': "Innov invoice 3.3",

    'summary': """
        This module use  guidelines or rules 
        issued by SAT, begin rules 3.3...""",

    'author': "Yonn, Xyz",
    'website': "https://innov.biz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # Catalog Sat
        'views/country.xml',
        'views/municipality.xml',
        #'data/res.country.municipality.csv',
        'views/locality.xml',
        #'data/res.country.locality.csv',
        'views/suburb.xml',
        ##'data/res.country.suburb.csv',
        'data/res.bank.csv',
        'views/product_code.xml',
        #this operation is slow 'data/product.code.csv',
        'views/product_unit.xml',
        'data/product.unit.csv',
        'views/merchandise_use.xml',
        'data/merchandise.use.csv',
        'views/way_pay.xml',
        'data/way.pay.csv',
        'views/type_document.xml',
        'data/type.document.csv',
        'views/type_relationship.xml',
        'data/type.relationship.csv',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/account_tax.xml',
        'data/type.tax.csv',
        'data/type.factor.csv',
        'data/payment.method.csv',
        'views/account_invoice.xml',

        # Inherits and switch catalog SAT
        'views/product_template.xml',
        'views/account_fiscal_position.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
     #   'demo/demo.xml',
    ],
}