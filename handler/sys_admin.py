import logging
import webapp2

import config
from handler.base import CRUDHandler
from model.account import UserRole
from utils.ndb_utils import *
from utils.handler_utils import *
from handler.auth import AuthHandler, verfication_route

class SysAdminHandler(CRUDHandler):
    @webapp2.cached_property
    def access_level(self):
        user_role = UserRole.query(UserRole.role_name == 'System Admin').get()
        return user_role.access_level

class PricePlanHandler(SysAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'price plan'
        super(PricePlanHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/sys_admin/price_plan'
        self.form['dt_source'] = 'PricePlan'
        self.model_cls = get_kind_by_name(self.form['dt_source'])  
        self.number_id = True
        
class BusinessGroupHandler(SysAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'business group'
        super(BusinessGroupHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/sys_admin/business_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.model_cls = get_kind_by_name(self.form['dt_source'])  
        self.number_id = True
        
class UserRoleHandler(SysAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'user role'
        super(UserRoleHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/sys_admin/user_role'
        self.form['dt_source'] = 'UserRole'
        self.model_cls = get_kind_by_name(self.form['dt_source']) 
        self.number_id = True
    
    def async_query_all_json(self):
        cond_list = [self.model_cls.access_level <= self.user.access_level]
        super(UserRoleHandler, self).async_query_all_json(cond_list)
        
    def post(self):
        form_access_level = self.request.get('access_level')
        if form_access_level and int(form_access_level) > self.user.access_level:
            msg = "You are not allowed to create this user role."
            self.async_render_msg(False, msg)
        else:
            super(UserRoleHandler, self).post()
        
class UserHandler(SysAdminHandler, AuthHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'user'
        super(UserHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/sys_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = get_kind_by_name(self.form['dt_source'])
        self.form['tb_buttons'] = 'create,edit,delete,export' 
        self.number_id = True
        
    def get(self):
        self.form['field_list'] = self.model_cls.get_form_fields()
        for field in self.form['field_list']:
            if field['prop_name'] == 'user_role':
                if self.user.user_role.get().role_name != 'Super Admin':
                    for choice in field['choices']:
                        if choice['text'] == 'Super Admin':
                            field['choices'].remove(choice)
        self.render("crud_form.html", form=self.form)
    
    def async_create(self):
        status , msg = self.create_new_user('vp')
        self.async_render_msg(status, msg)
        
    def async_edit(self):
        self.request.POST['user_access_level'] = self.user.access_level
        super(UserHandler, self).async_edit()

    def async_query_all_json(self):
        cond_list = [self.model_cls.access_level <= self.user.access_level]
        super(UserHandler, self).async_query_all_json(cond_list)
        
    def async_upload(self):
        self.async_render_msg(True, "Batch upload for user account is not allowed!")
        
            
app = webapp2.WSGIApplication([
    (r'/sys_admin/price_plan$', PricePlanHandler),
    (r'/sys_admin/business_group$', BusinessGroupHandler),
    (r'/sys_admin/user_role$', UserRoleHandler),
    (r'/sys_admin/users$', UserHandler),
    verfication_route,
], config=config.WSGI_CONFIG, debug=config.DEBUG)