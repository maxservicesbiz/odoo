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
from odoo import models, fields, api, exceptions
from .ct_mayorista_lib import CTMayoristaLib
import json
import requests
import base64
import logging
from odoo.tools.config import config
import uuid

_logger = logging.getLogger(__name__)
PREFIX_LOGGER = "Dropshipping CT: "

class InnovtDropshippingCTMayoristaSync(models.TransientModel):
    _name = 'innovt_dropshipping_ct_mayorista_sync'

    def get_ct(self):
        ct_api = self.env['res.config.settings'].sudo().get_ct_api()
        msg = "Agregue la cofiguración Web/Configuración/Ajuste/CT Mayorista"
        if len(ct_api):
            for k in ct_api.keys():
                if not ct_api.get(k):
                    field_empty = PREFIX_LOGGER + msg +"  Dato:" + k
                    _logger.error(field_empty)
                    raise exceptions.MissingError(field_empty)
        else:
            _logger.error(msg)
            raise exceptions.MissingError(msg)

        return CTMayoristaLib(
            ct_api.get('ct_api_url'),
            ct_api.get('ct_api_email'),
            ct_api.get('ct_api_user'),
            ct_api.get('ct_api_rfc'),

            ct_api.get('ct_ftp_host'),
            ct_api.get('ct_ftp_user'),
            ct_api.get('ct_ftp_password'),
        )

    @api.model
    def cron_do_task_product_sync(self, limit=0):
        ct = self.get_ct()
        path = config['data_dir'] + "/"
        products, ok = ct.products(path = path)
        _product_created = 0
        if not ok :
            for product in products:
                product_id = self.exists_product(product)                
                if len(product_id):
                    product_id = self.update_product(product_id, product)
                else:
                    product_id = self.create_product(product, ct)
                    _logger.info(PREFIX_LOGGER + "Product created {}/{}".format(
                        product_id.id,
                        product_id.name
                    ))
                    if limit:
                        _product_created += 1
                        if _product_created == limit:
                            break
        else:            
            _logger.error(PREFIX_LOGGER + " Fail download catalog FTP " +str(ok))

    @api.model
    def cron_do_task_product_stock_price(self, limit=0):
        ct = self.get_ct()
        rate = ct.rate()
        self._available_product_prices = []
        products = self.exists_product()
        warehouses = str(ct.get('ct_warehouses','')).split(',')        
        _product_updated = 0
        for product in products:            
            self.available_product(product, ct, rate, warehouses)
            if limit:
                _product_updated += 1
                if _product_updated == limit:
                    break

    @api.model
    def cron_do_task_product_feature_and_data_sheet(self, limit=0, force_update=False):
        ct = self.get_ct()
        products_ct, ok = ct.products(path = config['data_dir']+"/", catalog_exists=True)
        _product_fds = 0
        if not ok:            
            products_published = self.env.context.get('products_published', False) or self.env['product.template'].sudo().search([
                ('website_published','=',True),
                ('active','=',True)
            ])
            for product in products_published:
                updated = False
                #if not product.ct_features or not product.ct_data_sheet: 
                for seller in product.seller_ids:
                    if seller.name.id == self.cp_supplier().id:
                        for product_ct in products_ct:                            
                            if seller.product_code == product_ct.get('clave',''):                                
                                if not product.ct_features or force_update:
                                    action = self.product_url(product_ct)
                                    try:
                                        f = ct.features(action, config['data_dir'] )
                                        if len(f):
                                            f = f[0]
                                            product.ct_features = f.get('features')
                                            images = f.get('images')
                                            if hasattr(product, 'product_image_ids'):
                                                product_image_ids = []
                                                for image in images:
                                                    b64image = ct.get_image(image)
                                                    if b64image:                                                            
                                                        product_image_ids.append(
                                                            [0,'virtual_523',{
                                                                    'name': product.name +" "+str(uuid.uuid4()),
                                                                    'product_tmpl_id': product.id,
                                                                    'image': b64image, 
                                                                    #'__last_update': False,
                                                                }
                                                            ]
                                                        )
                                                product.write({'product_image_ids': product_image_ids})
                                            updated = True
                                    except Exception as e:
                                        _logger.error(PREFIX_LOGGER + " Fail get product features " +str(e))
                                if not product.ct_data_sheet or force_update:
                                    product_code = product_ct.get("clave")
                                    try:
                                        ds = ct.data_sheet(product_code, config['data_dir'] )
                                        if len(ds):
                                            ds = ds[0]
                                            product.ct_data_sheet = ds.get('data_sheet')
                                            updated = True
                                    except Exception as e:
                                        _logger.error(PREFIX_LOGGER + " Fail get product data sheet " +str(e))
                                if updated:
                                    _product_fds +=1
                                    if _product_fds == limit:
                                        return
        else:
            _logger.error(PREFIX_LOGGER + " Fail download catalog FTP " +str(ok))

    def product_url(self, product):
        return "{}/{}/{}/{}/{}".format(
            product.get("categoria").replace(' ','-'),
            product.get("subcategoria").replace(' ','-'),
            product.get("marca").replace(' ','-'),
            product.get("clave"),
            product.get("idProducto"),
        )
    
    def cp_price(self, product):
        price = False
        if product.get('moneda') != 'MXN':
            price = product.get('tipoCambio', 1) * product.get('precio', 1)
        else:
            price = product.get('precio', 1)
        return price

    def cp_specs(self, product):
        descripcion = ""
        spects = product.get('especificaciones', []) or []
        for spect in spects:
             descripcion +=  spect.get('tipo') +": "+spect.get('valor') + "\n"
        return descripcion

    def cp_image(self, product, ct):
        url = product.get('imagen',False)
        if url:
            return ct.get_image(url)
        return False

    def cp_public_category(self, product):
        category_vals = {
            'name': product.get('categoria', False),
            'sequence': 1
        }
        category = self.env['product.public.category'].sudo()
        cat_id = category.search([('name','=',category_vals.get('name'))], limit=1)
        if not len(cat_id):
            cat_id = category.create(category_vals)
        
        subcategory_vals = {
            'name': product.get('subcategoria', False),
            'parent_id': cat_id.id ,
            'sequence': 2
        }
        subcat_id = category.search([('name','=',subcategory_vals.get('name'))], limit=1)
        if not len(subcat_id):
            subcat_id = category.create(subcategory_vals)
        
        brand_base_id = category.search([('name','=','Marca')], limit=1)
        if not len(brand_base_id):
            brand_base_id = category.create({
                'name':'Marca', 
                'sequence': 10
            })

        brand_vals = {
            'name': product.get('marca', False),
            'parent_id': brand_base_id.id,
            'sequence': 4,
        }        
        brand_id = category.search([('name','=',brand_vals.get('name'))], limit=1)
        if not len(brand_id):
            brand_id = category.create(brand_vals)

        return [
            [6,False,[subcat_id.id or cat_id.id, brand_id.id]]
        ]

    def cp_route(self, product):
        dropshipping_id = self.env.ref('stock_dropshipping.route_drop_shipping')
        #dropshipping_id = self.env.ref('purchase.route_warehouse0_buy')
        return [
            [6,False,[dropshipping_id.id]]
        ]

    def cp_category(self, product):
        category_id = self.env.ref('product.product_category_all')

        category_vals = {
            'name': product.get('categoria', False),
            'parent_id': category_id.id 
        }
        category = self.env['product.category'].sudo()
        cat_id = category.search([('name','=',category_vals.get('name'))], limit=1)
        if not len(cat_id):
            cat_id = category.create(category_vals)
        
        subcategory_vals = {
            'name': product.get('subcategoria', False),
            'parent_id': cat_id.id             
        }
        subcat_id = category.search([('name','=',subcategory_vals.get('name'))], limit=1)
        if not len(subcat_id):
            subcat_id = category.create(subcategory_vals)
        return subcat_id.id or cat_id.id or category_id.id

    def cp_supplier(self):
        supplier = {
            'name': 'CT Internacional del Noroeste S.A. DE C.V.',
            'company_type': 'company',
            'vat': 'CIN960904FQ2',
            'street': 'Guerrero #168',
            'city': 'Hermosillo',
            'zip': '83000',
            'state_id': self.env.ref('base.state_mx_son').id or False,
            'country_id': self.env.ref('base.mx').id or False,
        }
        res_partner = self.env['res.partner'].sudo()
        supplier_id = res_partner.search([('vat','=', supplier.get('vat'))])
        if not len(supplier_id):
            supplier_id = res_partner.create(supplier)
        return supplier_id

    def cp_seller(self, product):
            
        currency_id = self.env.ref('base.' + product.get('moneda'))
        seller = [
            [
                0,
                "virtual_1297",
                {
                    #"delay": 1,
                    #"product_tmpl_id": false,
                    #"min_qty": 100,
                    "price": product.get('precio'),
                    "currency_id": currency_id.id,
                    "company_id": self.env.user.company_id.id,
                    #"product_id": false,
                    "name": self.cp_supplier().id,
                    "product_name": product.get('nombre'),
                    "product_code": product.get('clave'),
                    #"date_start": false,
                    #"date_end": false,
                    #"sequence": 0
                }
            ]
        ]

        return seller

    def cp_dimensions(self, product, ct):
        dimensions = {
            'plong': False,
            'phigh': False,
            'pwidth': False,
            'weight': False
        }
        return dimensions
        """ 
            TODO: This action block maxs request API
        """
        try:
            data = ct.product_dimensions(product.get('clave'))            
            if len(data):
                dimensions.update({
                    'plong': data[0].get('largo'),
                    'phigh': data[0].get('alto'),
                    'pwidth': data[0].get('ancho'),
                    'weight': data[0].get('peso')
                })
        except Exception as e:
            _logger.error( PREFIX_LOGGER + "Fail product dimensions" + str(e))
        return dimensions

    def create_product(self, product, ct):
        dimensions = self.cp_dimensions(product, ct)

        product2create = {
        
        "name": product.get('nombre'),

        "active": True if product.get('activo') else False ,
        "sale_ok": True,
        "purchase_ok": True,
        "type": "product",
        
        "list_price": self.cp_price(product),
        "categ_id": self.cp_category(product),

        'mpn': product.get('numParte'),
        'ean': product.get('ean'),
        'upc': product.get('upc'),

        #"property_cost_method": false,
        #"company_id": 1,  default
        #"uom_id": 20,
        #"uom_po_id": 20,
        #"inventory_availability": "never",
        #"available_threshold": 0,
        #"custom_message": "",
        #"unidad_medida": "Pieza",
        "route_ids": self.cp_route(product),
        #"sale_delay": 3,
        #"responsible_id": 1,
        #"tracking": "none",
        #"property_stock_production": 7,
        #"property_stock_inventory": 5,
        #"taxes_id": [
        #    [
        #        6,
        #        false,
        #        [
        #            2
        #        ]
        #    ]
        #],
        #"property_account_income_id": false,
        #"supplier_taxes_id": [
        #    [
        #        6,
        #        false,
        #        [
        #            10
        #        ]
        #    ]
        #],
        #"property_account_expense_id": false,
        #"property_account_creditor_price_difference": false,
        #"property_valuation": false,
        #"property_stock_account_input": false,
        #"property_stock_account_output": false,
        #"split_method": "equal",
        #"invoice_policy": "order",
        #"service_type": "manual",
        #"service_tracking": "no",
        #"project_id": false,
        #"expense_policy": "no",
        #"purchase_method": "purchase",
        #"sale_line_warn": "no-message",
        #"purchase_line_warn": "no-message",
        #"website_published": True,
        "image_medium": self.cp_image(product, ct),
        #"__last_update": false,
        #
        #"can_be_expensed": false,
        #"default_code": "Referencia interna\t",
        #"barcode": "C\u00f3digo de barras\t",
        #"hs_code": "C\u00f3digo HS\t",
        #"standard_price": 890,
        "public_categ_ids": self.cp_public_category(product),    
        #"alternative_product_ids": [
        #    [
        #        6,
        #        false,
        #        [
        #            699
        #        ]
        #    ]
        #],
        #"accessory_product_ids": [
        #    [
        #        6,
        #        false,
        #        [
        #            930
        #        ]
        #    ]
        #],
        #"optional_product_ids": [
        #    [
        #        6,
        #        false,
        #        [
        #            699
        #        ]
        #    ]
        #],
        #"website_style_ids": [
        #    [
        #        6,
        #        false,
        #        []
        #    ]
        #],
        "seller_ids": self.cp_seller(product),
        #"clave_producto": false,
        #"weight": 0,
        #"volume": 0,
        #"landed_cost_ok": false,
        #"service_policy": false,
        "description": product.get('descripcion_corta'),
        "description_sale": self.cp_specs(product),
        #"description_purchase": "Descripci\u00f3n para proveedores\n",
        #"description_pickingout": "Descripci\u00f3n para pedidos de entrega\n",
        #"description_pickingin": "Descripci\u00f3n para Recepciones\n",
        #"description_picking": "Descripci\u00f3n para Transferencias Internas\n"
        }
        product_id = self.env['product.template'].sudo().create(product2create)
        return product_id

    def exists_product(self, product=False):
        if product:
            return self.env['product.template'].sudo().search([
                ('seller_ids.name','=',self.cp_supplier().id),
                ('seller_ids.product_code','=',product.get('clave'))
            ], limit = 1)
        else:
            return self.env['product.template'].sudo().search([
                ('seller_ids.name','=',self.cp_supplier().id),
                ('active','=',True)
            ])

    def update_product(self, product_id, product):
        return product_id
       
    def available_product(self, product, ct, rate, warehouses):
        for seller in product.seller_ids:
            if seller.name.id == self.cp_supplier().id:
                product_code = seller.product_code    
                _logger.info(
                    PREFIX_LOGGER + "Product update: {}/{}".format(
                        product_code, product.name                        
                    )
                )
                try:
                    # TODO: Sync price optimized 
                    price = self.available_product_price(product_code, ct, rate)
                    last_price = product.list_price
                    new_price = self.cp_price(price)
                    if last_price !=  new_price:
                        product.list_price = new_price
                    _logger.info( PREFIX_LOGGER + "Last price:{} New price:{}".format( last_price, new_price))

                    # TODO: Sync prices slowly
                    #price =  ct.product_price(product_code)            
                    #if len(price):
                    #    price.update(rate)
                    #    new_price = self.cp_price(price)
                    #    last_price = product.list_price
                    #    if last_price !=  new_price:
                    #        product.list_price = new_price
                    #    print("Last price:", last_price, "New price:", new_price)
                    #else:
                    #    raise Exception("Not found price")
                except Exception as e : 
                    _logger.error( PREFIX_LOGGER + "Product price update " + str(e))

                try:
                    stock = ct.product_stock(product_code)
                    if len(stock):
                        #warehouses =  ['01A','02A']
                        for warehouse in warehouses:
                            stock_data = stock.get(warehouse, False)                    
                            if stock_data :
                                last_status = product.website_published
                                if stock_data.get('existencia', 0) == 0:
                                    product.website_published = False
                                else:
                                    product.website_published = True
                                    _logger.info( PREFIX_LOGGER + "Last status:{} New status:{} ".format(last_status, product.website_published))
                                    break
                    else:
                        raise Exception("Not found stock")
                except Exception as e: 
                    _logger.error( PREFIX_LOGGER + "Product stock update " + str(e))
                break # if exists supllier

    _available_product_prices = []

    def available_product_price(self, product_code, ct, rate):
        if not len(self._available_product_prices):
            self._available_product_prices = ct.product_price()
        
        if len(self._available_product_prices):            
            for p in self._available_product_prices:
                if p.get('clave') == product_code:
                    data = p.update(rate)
                    return data
            raise Exception("Not found price")
        else:
            raise Exception("the list product_prices is empty, fail request API")


        