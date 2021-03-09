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

import datetime
import requests
from ftplib import FTP
import logging
import json
from urllib.parse import urljoin
import os 
import subprocess
import base64

_logger = logging.getLogger(    __name__)

class CTMayoristaLib(object):
    
    token_hash = False
    token_time = False

    def __init__(self, api_url, api_email, api_user, api_rfc, ftp_host, ftp_user, ftp_password):
        self.api_url=api_url 
        self.api_email=api_email
        self.api_user=api_user
        self.api_rfc=api_rfc 
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_password = ftp_password

    def http_call(self, url, method, **kwargs):
        refresh_token = kwargs.pop('refresh_token')        
        self.get_token_hash(refresh_token)
        if 'headers' in kwargs:
            kwargs.get('headers', {}).update(self.headers())            
        else:
            kwargs['headers'] = self.headers()
        try:            
            start_time = datetime.datetime.now()
            response = requests.request(method, url, **kwargs)
            duration = datetime.datetime.now() - start_time
            if response.ok:
                return response.json(), False
            else:
                raise Exception(response.content)
        except Exception as e:
            return False, e
        return False, Exception("Fail http call")

    def headers(self):        
        header = {            
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "Innovt-Dropshipping"
        }
        if self.token_hash:
            header.update({"x-auth": self.token_hash })
        return header
    
    def get_token_hash(self, refresh_token):
        if refresh_token:
            params = {
                'email': self.api_email,
                'cliente':self.api_user,
                'rfc': self.api_rfc,
            }

            if not self.token_time:
                self.token_time = datetime.datetime.now() - datetime.timedelta(days=1)
            
            if self.token_time > datetime.datetime.now():            
                if self.token_hash is not None:
                    return self.token_hash

            token, ok = self.post('/cliente/token', params=params, refresh_token=False)
            if not ok:
                self.token_hash = token.get('token')
                self.token_time = datetime.datetime.strptime(token.get('time'), '%Y-%m-%dT%H:%M:%S.%fZ')
                return self.token_hash
            else:
                raise ok
    
    def get(self, action, headers=None, refresh_token=True):
        return self.http_call(
            urljoin(self.api_url, action),
            'GET',
            headers=headers or {},
            refresh_token=refresh_token
        )
    
    def post(self, action, params=None, headers=None, refresh_token=True):
        return self.http_call(
            urljoin(self.api_url, action),
            'POST',
            json=params or {},
            headers=headers or {},
            refresh_token=refresh_token
        )

    def products(self, path= "/tmp/", catalog_exists=False):
        if catalog_exists:
            product = "productos.json"
            url = urljoin(path, product)
            if os.path.exists(url):
                try:             
                    with open(url) as json_file:
                        data = json.load(json_file)
                        return data, None
                except Exception as e:
                    return None, Exception("Error load producto.json " + str(e))

        ftp = FTP(self.ftp_host)        
        ftp.login(self.ftp_user,self.ftp_password)
        ftp.cwd('catalogo_xml')
        files = ftp.nlst()
        except_str = ""
        for filename in files:
            try:
                if 'productos.json' == filename:                    
                    if os.path.exists(path+filename):
                        os.remove(path+filename)
                    fhandle = open(path+filename, 'wb')                    
                    ftp.retrbinary('RETR ' + filename, fhandle.write)
                    fhandle.close()
                    with open(path+filename) as json_file:
                        data = json.load(json_file)
                        return data, None
            except Exception as e:
                except_str += str(e)
        ftp.quit()

        return None, Exception("FTP error:" + except_str)

    def product_dimensions(self, product_code):
        data, ok =self.get('/paqueteria/volumetria/'+ product_code)
        if ok: 
            raise ok
        return  data

    def product_price(self, product_code=False):
        url = '/existencia/promociones'
        if product_code:
            url += '/'+product_code
        data, ok =self.get(url)
        if ok: 
            raise ok
        return  data

    def product_stock(self, product_code, warehouse_code=False):
        url = '/existencia/'+product_code
        if warehouse_code :
            url += '/'+warehouse_code
        data, ok =self.get(url)
        if ok: 
            raise ok
        return data

    def rate(self ):
        data, ok =self.get('/pedido/tipoCambio')
        if ok: 
            raise ok
        return  data

    def features(self, action, path):
        dir_path = os.path.dirname(os.path.realpath(__file__))        
        ct_features_out = path+"/ct_features.json"
        if os.path.exists(ct_features_out):
            os.remove(ct_features_out)
        subprocess.call(
            [
                'scrapy',
                 'runspider',                  
                 dir_path+'/ct_product_features_scrapy.py',
                 '-a', 'path='+action,
                 '-t', 'json',
                 '-o',  ct_features_out,
                 '--nolog'
            ]
        )
        with open(ct_features_out) as json_file:
            data = json.load(json_file)
            json_file.close()
            os.remove(ct_features_out)
            return data
        return None

    def data_sheet(self, product_code, path):
        dir_path = os.path.dirname(os.path.realpath(__file__))        
        ct_data_sheet_out = path+"/ct_data_sheet.json"
        if os.path.exists(ct_data_sheet_out):
            os.remove(ct_data_sheet_out)
        subprocess.call(
            [
                'scrapy',
                 'runspider',                  
                 dir_path+'/ct_product_data_sheet_scrapy.py',
                 '-a', 'product_code='+product_code,
                 '-t', 'json',
                 '-o',  ct_data_sheet_out,
                 '--nolog'
            ]
        )
        with open(ct_data_sheet_out) as json_file:
            data = json.load(json_file)
            json_file.close()
            os.remove(ct_data_sheet_out)
            return data
        return None
        
    def get_image(self, url):        
        try:
            result = requests.get(url, verify=False, timeout=20)
            if result.status_code == 200:
                return base64.b64encode(result.content)
        except Exception as e:
            pass
        return False
