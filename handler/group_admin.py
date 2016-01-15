import webapp2
import logging
import config

from handler.auth import verfication_route
from handler.role_access import UserHandler, GroupAdminHandler
from model.account import *
from model.base_doc import AddressDocument


'''class GroupOperationHandler(GroupAdminHandler):
    def init_form_data(self):
        self.init_handler_data('group_admin')

class GroupAreaHandler(GroupOperationHandler):
    def init_handler_data(self, handler_url):
        self.page_name = 'Area'
        self.form['action'] = '/'+handler_url+'/area'
        self.form['dt_source'] = 'Area'
        self.model_cls = Area
'''
        
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
        self.is_audit = True
        self.audit_event_key = 'email_lower' 
        
    '''def async_query_all_json(self):
        cond_list = [User.business_group == self.user.business_group]
        UserHandler.async_query_all_json(self, cond_list=cond_list)
    '''
        
    '''def post(self):
        self.request.POST['business_group'] = str(self.business_group_id)
        super(GroupAdminUserHandler, self).post()
    '''    
class BusinessGroupHandler(GroupAdminHandler):
    def init_form_data(self):
        self.page_name = 'Group Profile'
        self.form['action'] = '/group_admin/business_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.model_cls = BusinessGroup 
        self.edit_exclude_list = ['price_plan', 'status', 'expiry_date', 'last_payment']
        self.is_audit = True
        self.audit_event_key = 'business_name'
    
    def get(self):
        model_entity = self.user.business_group.get()
        self.get_edit(model_entity)
        
class BusinessTeamHandler(GroupAdminHandler):
    def init_form_data(self):
        self.page_name = 'Business Team'
        self.form['action'] = '/group_admin/business_team'
        self.form['dt_source'] = 'BusinessTeam'
        self.model_cls = BusinessTeam
        self.is_audit = True
        self.audit_event_key = 'team_name'

        
    def process_get_form_data(self, form_data):
        form_data = self.set_default_country(form_data)
        form_data = super(BusinessTeamHandler, self).process_get_form_data(form_data)
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
    
class AuditLogHandler(GroupAdminHandler):
    def init_form_data(self):
        self.page_name = 'audit log'
        self.form['action'] = '/group_admin/audit_log'
        self.form['dt_source'] = 'AuditLog'
        self.model_cls = AuditLog 
        self.form['tb_buttons'] = 'export'
               
app = webapp2.WSGIApplication([
    (r'/group_admin/business_group$', BusinessGroupHandler),
    (r'/group_admin/users$', GroupAdminUserHandler),
    (r'/group_admin/business_team$', BusinessTeamHandler),
    (r'/group_admin/audit_log$', AuditLogHandler),
    verfication_route, 
], config=config.WSGI_CONFIG, debug=config.DEBUG)        