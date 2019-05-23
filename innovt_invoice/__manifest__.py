{
    'name': "Innovt Invoice",

    'summary': """
        This module use  guidelines or rules 
        issued by SAT, begin rules 3.3...""",

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
        'contacts',
        'product',
        'innovt_client',
        'account_invoicing',
        'l10n_mx',
        'base_vat_autocomplete'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',

        'views/catalogs/country.xml',
        'views/catalogs/municipality.xml',
        'views/catalogs/locality.xml',
        'views/catalogs/suburb.xml',
        'views/catalogs/product_code.xml',
        'views/catalogs/product_unit.xml',
        'views/catalogs/cfdi_use.xml',
        'views/catalogs/payment_form.xml',
        #'views/catalogs/type_document.xml',
        'views/catalogs/type_relationship.xml',
        'views/catalogs/account_tax.xml',

        # Inherits and switch catalog SAT
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/account_invoice.xml',
        'views/product_template.xml',
        'views/account_fiscal_position.xml',
        'views/reports/cfdi.xml',
        'data/mail_template_cfdi_invoice_data.xml',
        'data/cron_check_invoice_cancellation_process_data.xml',
        'wizard/import_cfdi_to_invoice_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
     #   'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
