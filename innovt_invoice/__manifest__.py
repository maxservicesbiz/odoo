{
    'name': "Innov Invoice",

    'summary': """
        This module use  guidelines or rules 
        issued by SAT, begin rules 3.3...""",

    'author': "Yonn, Xyz",
    'website': "https://innov.biz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'contacts',
        'product',
        'innovt_client',
        'account_invoicing',
        'l10n_mx',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # Catalog Sat
        'views/catalogs/country.xml',
        'views/catalogs/municipality.xml',
        #'data/catalogs/res.country.municipality.csv',
        'views/catalogs/locality.xml',
        #'data/catalogs/res.country.locality.csv',
        'views/catalogs/suburb.xml',
        ##'data/catalogs/res.country.suburb.csv',
        'data/catalogs/res.bank.csv',
        'views/catalogs/product_code.xml',
        #this operation is slow
        #'data/catalogs/product.code.csv',
        'views/catalogs/product_unit.xml',
        #this operation is slow
        #'data/catalogs/product.unit.csv',
        'views/catalogs/cfdi_use.xml',
        'data/catalogs/cfdi.use.csv',
        'views/catalogs/payment_form.xml',
        'data/catalogs/payment.form.csv',
        #'views/catalogs/type_document.xml',
        #'data/catalogs/type.document.csv',
        'views/catalogs/type_relationship.xml',
        'data/catalogs/type.relationship.csv',
        'views/catalogs/account_tax.xml',
        'data/catalogs/type.factor.csv',
        'data/catalogs/type.tax.csv',
        'data/catalogs/payment.method.csv',

        # Inherits and switch catalog SAT
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/account_invoice.xml',
        'views/product_template.xml',
        'views/account_fiscal_position.xml',

        'views/reports/cfdi.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
     #   'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
