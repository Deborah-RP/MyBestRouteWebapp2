import logging
import webapp2
import json

from google.appengine.api import urlfetch
#from google.appengine.api import taskqueue
from google.appengine.ext import deferred


import config
from handler.auth import verfication_route
from handler.role_access import UserHandler, SuperAdminHandler
from model.base_model import FormField
from model.base_doc import SGAdressDocument
from model.account import UserRole, User, AuditLog
from model.plan import Address

class InitConfigFormHandler(SuperAdminHandler):
    def init_form_data(self):
        self.form['dt_source'] = 'FormField'
        self.model_cls = FormField
    
    def get(self):
        self.render('init_config_form.html')
        
class ConfigFormHandler(SuperAdminHandler):
    def init_form_data(self):
        self.page_name = 'form field'
        #self.form['header'] = 'HTML Form Configuration'
        self.form['action'] = '/super_admin/config_form'
        self.form['dt_source'] = 'FormField'
        self.model_cls = FormField
        
class InitPostalSearch(SuperAdminHandler):
    def init_form_data(self):
        self.page_name = 'address'
        self.form['action'] = '/super_admin/update_postal'
        self.form['dt_source'] = 'Address'
        self.model_cls = Address  
        
    def get(self):
        self.render('init_sg_postal.html')
           
    def post(self):
        #Delete all the old items in the index
        SGAdressDocument.delete_all_in_index()
        #10 json files contains the address info
        for i in range(10):
            jsonUrl = "https://s3-ap-southeast-1.amazonaws.com/clt-friso/%dpostal.json" % i
            logging.info("Downloading json file %d" %i)
            urlfetch.set_default_fetch_deadline(40)
            result = urlfetch.fetch(jsonUrl)
            
            if result.status_code == 200:
                postal_data = json.loads(result.content)    
                logging.info("File loaded, total %d items.\n" % len(postal_data))
                chunks=[postal_data[x:x+100] for x in xrange(0, len(postal_data), 100)]
                i = 1
                for chunk in chunks:
                    deferred.defer(SGAdressDocument.build_doc_batch, chunk)

            else:
                logging.critical("File %d not found" % i)
                
class UserRoleHandler(SuperAdminHandler):
    def init_form_data(self):
        self.page_name = 'user role'
        self.is_audit = True
        self.audit_event_key = 'role_name'
        self.form['action'] = '/super_admin/user_role'
        self.form['dt_source'] = 'UserRole'
        self.model_cls = UserRole
        self.form['tb_buttons'] = 'create,edit,delete,export'
    
    def async_query_all_json(self):
        cond_list = [UserRole.access_level <= self.user.access_level]
        super(UserRoleHandler, self).async_query_all_json(cond_list=cond_list)
        
    def post(self):
        form_access_level = self.request.get('access_level')
        if form_access_level and int(form_access_level) > self.user.access_level:
            msg = "You are not allowed to create role which has higher access level than your own."
            response = {}
            response['status'] = False
            response['message'] = msg
            self.async_render_msg(response)
        else:
            super(UserRoleHandler, self).post()
            
    def async_upload(self):
        response = {}
        response['status'] = True
        response['message'] = "Batch upload for user role is not allowed!"
        self.async_render_msg(response)            

class SuperAdminUserHandler(SuperAdminHandler, UserHandler):
    def init_form_data(self):
        self.page_name = 'user'
        self.form['action'] = '/super_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = User
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.max_user_level = config.SUPER_ADMIN.access_level
        self.min_user_level = config.GROUP_ADMIN.access_level
        self.is_audit = True
        self.audit_event_key = 'email_lower'
        self.create_exclude_list = ['business_team']
        self.edit_exclude_list = ['business_team']
        self.form_exclude_list = ['business_team']
                    
app = webapp2.WSGIApplication([
    (r'/super_admin/init_config_form$', InitConfigFormHandler),
    (r'/super_admin/config_form$', ConfigFormHandler),
    (r'/super_admin/init_postal$', InitPostalSearch),
    (r'/super_admin/user_role$', UserRoleHandler),
    (r'/super_admin/users$', SuperAdminUserHandler), 
   verfication_route,
], config=config.WSGI_CONFIG, debug=config.DEBUG)