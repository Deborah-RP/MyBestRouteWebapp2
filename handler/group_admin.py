import webapp2

import config
from handler.base import CRUDHandler
from handler.auth import verfication_route
from handler.role_access import UserHandler, GroupAdminHandler
from model.account import *
from model.plan import *

class AreaHandler(GroupAdminHandler):
    def init_form_data(self):
        self.page_name = 'Area'
        self.form['action'] = '/group_admin/area'
        self.form['dt_source'] = 'Area'
        self.model_cls = Area
            
class GroupAdminUserHandler(GroupAdminHandler, UserHandler):
    def init_form_data(self):
        self.page_name = 'user'
        self.form['action'] = '/group_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = User
        self.form_exclude_list = ['business_group', 'email_lower', 'price_plan']
        self.table_exclude_list = ['_entity_id', 'access_level']
        self.create_exclude_list = ['email_lower', 'price_plan']
        self.edit_exclude_list = ['email_lower', 'price_plan']
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.max_user_level = config.GROUP_ADMIN.access_level
        self.min_user_level = config.TEAM_USER.access_level        
        
    def async_query_all_json(self):
        cond_list = [User.business_group == self.user.business_group]
        UserHandler.async_query_all_json(self, cond_list=cond_list)
        
    '''def post(self):
        self.request.POST['business_group'] = str(self.business_group_id)
        super(GroupAdminUserHandler, self).post()
    '''    
class BusinessGroupHandler(GroupAdminHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'Group Profile'
        super(BusinessGroupHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/group_admin/business_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.model_cls = BusinessGroup 
        self.edit_exclude_list = ['price_plan', 'status', 'expiry_date', 'last_payment']
    
    def get(self):
        model_entity = self.user.business_group.get()
        self.get_edit(model_entity)
        
class BusinessTeamHandler(GroupAdminHandler):
    def init_form_data(self):
        self.page_name = 'Business Team'
        self.form['action'] = '/group_admin/business_team'
        self.form['dt_source'] = 'BusinessTeam'
        self.model_cls = BusinessTeam
        
    def process_get_form_data(self, form_data):
        field_list = form_data['field_list']
        for each in field_list:
            if each['prop_name'] == 'country':
                each['default_value'] = self.user.business_group.get().country
        return form_data
        
    '''def post(self):
        self.request.POST['business_group'] = str(self.business_group_id)
        self.request.POST['user_created'] = str(self.user.key.id())
        super(BusinessTeamHandler, self).post()
    '''
        
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each['business_group'] = self.user.business_group
            each['user_created'] = self.user.key
        return upload_data
        
app = webapp2.WSGIApplication([
    (r'/group_admin/business_group$', BusinessGroupHandler),
    (r'/group_admin/users$', GroupAdminUserHandler),
    (r'/group_admin/business_team$', BusinessTeamHandler),
    (r'/group_admin/area$', AreaHandler),
    verfication_route, 
], config=config.WSGI_CONFIG, debug=config.DEBUG)        