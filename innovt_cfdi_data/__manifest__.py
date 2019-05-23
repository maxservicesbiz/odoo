{
    'name': "Innovt Cfdi Data",

    'summary': """
        This module only install data the models: 
        
        """,

    'author': "Max Solutions, Co",
    'website': "https://max-solutions.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'innovt_invoice',
        'innovt_payment',
    ],

    # always loaded
    'data': [
        
        # Catalog Sat
        #'data/catalogs/res.country.municipality.csv',
        #'data/catalogs/res.country.locality.csv',
        ##'data/catalogs/res.country.suburb.csv',
        'data/catalogs/res_bank_data.xml',
        #this operation is slow
        'data/catalogs/product_code_data.xml',
        #this operation is slow
        'data/catalogs/product_unit_data.xml',
        'data/catalogs/cfdi_use_data.xml',
        'data/catalogs/payment_form_data.xml',
        #'data/catalogs/type.document.csv',
        'data/catalogs/type_relationship_data.xml',
        'data/catalogs/type_factor_data.xml',
        'data/catalogs/type_tax_data.xml',
        'data/catalogs/payment_method_data.xml',
        #'data/catalogs/account_fiscal_position_data.xml',
    ],
    # Only loaded in demonstration mode
    'demo': [
        
    ],
}
# -*- coding: utf-8 -*-
