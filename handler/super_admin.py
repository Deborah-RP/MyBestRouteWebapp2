import logging
import webapp2

import config
from handler.base import CRUDHandler
from config import DEBUG
from model.base_model import FormField
from model.account import UserRole
from utils.ndb_utils import *
from utils.handler_utils import *


class SuperAdminHandler(CRUDHandler):
    @webapp2.cached_property
    def access_level(self):
        user_role = UserRole.query(UserRole.role_name == 'Super Admin').get()
        return user_role.access_level

class InitConfigFormHandler(SuperAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'form field'
        super(InitConfigFormHandler, self).__init__(*arg, **kwargs)
        self.form['dt_source'] = 'FormField'
        self.model_cls = get_kind_by_name(self.form['dt_source'])   
    
    def get(self):
        self.render('init_config_form.html')
        
class ConfigFormHandler(SuperAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'form field'
        super(ConfigFormHandler, self).__init__(*arg, **kwargs)
        self.form['header'] = 'HTML Form Configuration'
        self.form['action'] = '/super_admin/config_form'
        self.form['dt_source'] = 'FormField'
        self.model_cls = get_kind_by_name(self.form['dt_source'])   
            
app = webapp2.WSGIApplication([
    (r'/super_admin/init_config_form$', InitConfigFormHandler),
    (r'/super_admin/config_form$', ConfigFormHandler),
], config=config.WSGI_CONFIG, debug=config.DEBUG)