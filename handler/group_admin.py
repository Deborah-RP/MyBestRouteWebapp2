import webapp2

import config
from handler.base import CRUDHandler
from handler.auth import AuthHandler, verfication_route
from model.account import User, UserRole
from utils.ndb_utils import *

class GroupAdminHandler(CRUDHandler):
    @webapp2.cached_property
    def access_level(self):
        user_role = UserRole.query(UserRole.role_name == 'Group Admin').get()
        return user_role.access_level
    
    @webapp2.cached_property
    def business_id(self):
        return self.user.business_group.get().key.id()
        
class UserHandler(GroupAdminHandler, AuthHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'user'
        super(UserHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/group_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = get_kind_by_name(self.form['dt_source']) 
        self.number_id = True
        self.form_exclude_list = ['business_group', 'email_lower', 'price_plan']
        self.create_exclude_list = ['email_lower', 'price_plan']
        self.edit_exclude_list = ['email_lower', 'price_plan']
        self.form['tb_buttons'] = 'create,edit,delete,export'
        
    def async_create(self):
        status , msg = self.create_new_user('vp')
        self.async_render_msg(status, msg)
        
    def async_query_all_json(self):
        cond_list = [User.business_group == self.user.business_group, User.access_level <= self.access_level]
        super(UserHandler, self).async_query_all_json(cond_list)
        
    def get(self):
        self.form['field_list'] = self.model_cls.get_form_fields(None, self.form_exclude_list)
        for field in self.form['field_list']:
            if field['prop_name'] == 'user_role':
                idx = 0
                while idx < len(field['choices']):
                    if field['choices'][idx]['text'] not in ['Group Admin', 'Group User']:
                        field['choices'].pop(idx)
                        idx = idx -1
                    idx = idx+1
                #field['choices'] = ['Group Admin', 'Group User']
        self.render("crud_form.html", form=self.form)
        
    def post(self):
        self.request.POST['business_group'] = self.business_id
        super(UserHandler, self).post()
        
    def async_edit(self):
        self.request.POST['user_access_level'] = self.user.access_level
        super(UserHandler, self).async_edit()
    
    def async_upload(self):
        self.async_render_msg(True, "Batch upload for user account is not allowed!")    

class BusinessGroupHandler(GroupAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'Group Profile'
        super(BusinessGroupHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/group_admin/business_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.model_cls = get_kind_by_name(self.form['dt_source'])  
        self.number_id = True
        self.edit_exclude_list = ['price_plan', 'status', 'expiry_date', 'last_payment']
    
    def get(self):
        model_entity = self.user.business_group.get()
        self.get_edit(model_entity)
            
app = webapp2.WSGIApplication([
    (r'/group_admin/business_group$', BusinessGroupHandler),
    (r'/group_admin/users$', UserHandler),
    verfication_route, 
], config=config.WSGI_CONFIG, debug=config.DEBUG)        