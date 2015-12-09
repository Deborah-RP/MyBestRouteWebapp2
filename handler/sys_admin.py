import logging
import webapp2

import config
from handler.base import CRUDHandler
from model.account import *
from utils.handler_utils import *
from handler.auth import verfication_route
from handler.user import UserHandler

class SysAdminHandler(CRUDHandler):
    @webapp2.cached_property
    def min_access_level(self):
        user_role = UserRole.query(UserRole.role_name == config.SYS_ADMIN).get()
        return user_role.access_level

class PricePlanHandler(SysAdminHandler):
    def init_form_data(self):
        self.repeat_field_list = ['plan_modules']
        self.page_name = 'price plan'
        self.form['action'] = '/sys_admin/price_plan'
        self.form['dt_source'] = 'PricePlan'
        self.model_cls = PricePlan  
       
class BusinessGroupHandler(SysAdminHandler):
    def init_form_data(self):
        self.page_name = 'business group'
        self.form['action'] = '/sys_admin/business_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.model_cls = BusinessGroup 
        
class SysAdminUserHandler(SysAdminHandler, UserHandler):
    def init_form_data(self):
        self.page_name = 'user'
        self.form['action'] = '/sys_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = User
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.max_user_level = self.get_access_level(config.SYS_ADMIN)
        self.min_user_level = self.get_access_level(config.GROUP_ADMIN)
        self.create_exclude_list = ['business_team']
        self.edit_exclude_list = ['business_team']
        self.form_exclude_list = ['business_team']
            
app = webapp2.WSGIApplication([
    (r'/sys_admin/price_plan$', PricePlanHandler),
    (r'/sys_admin/business_group$', BusinessGroupHandler),
    (r'/sys_admin/users$', SysAdminUserHandler),
    verfication_route,
], config=config.WSGI_CONFIG, debug=config.DEBUG)