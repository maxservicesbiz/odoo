from odoo import http
import logging
from odoo.addons.web.controllers.main import ensure_db
import pprint


_logger = logging.getLogger(__name__)

class HealthCheckController(http.Controller):
    
    @http.route(['/health'], type='http', auth='public', method=['GET'])
    def _health(self, **post):
        ensure_db()
        return http.request.make_response("ok")
    
    @http.route(['/ping'], type='http', auth='public', method=['GET'])
    def _ping(self, **post):
        return http.request.make_response("ok")
        
    