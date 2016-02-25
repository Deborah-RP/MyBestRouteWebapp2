import logging
import webapp2



import config

from handler.auth import verfication_route
from handler.role_access import TeamHandler, UserHandler
from model.account import AuditLog, User
from model.plan import ClientAccount

class TeamAdminUserHandler(TeamHandler, UserHandler):
    def init_form_data(self):
        self.page_name = 'user'
        self.form['action'] = '/team_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = User
        self.form_exclude_list = ['business_group', 'business_team', 'email_lower', 'price_plan']
        self.table_exclude_list = ['_entity_id', 'access_level']
        self.create_exclude_list = ['email_lower', 'price_plan']
        self.edit_exclude_list = ['email_lower', 'price_plan']
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.max_user_level = config.TEAM_ADMIN.access_level
        self.min_user_level = config.TEAM_USER.access_level       
        self.is_audit = True
        self.audit_event_key = 'email_lower' 

class AuditLogHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'audit log'
        self.form['action'] = '/team_admin/audit_log'
        self.form['dt_source'] = 'AuditLog'
        self.model_cls = AuditLog 
        self.form['tb_buttons'] = 'export'
        
class ClientAccountHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'Client Account'
        self.form['action'] = '/team_admin/set/client_account'
        self.form['dt_source'] = 'ClientAccount'
        self.repeat_field_list = ['notify_added', 'notify_deleteded',
                                  'notify_finalized', 'notify_failed',
                                  'notify_partial', 'notify_lapsed']
        self.model_cls = ClientAccount

        self.is_audit = True
        self.audit_event_key = 'acct_name'        
        
app = webapp2.WSGIApplication([
    (r'/team_admin/users$', TeamAdminUserHandler),                               
    (r'/team_admin/audit_log$', AuditLogHandler),
    (r'/team_admin/set/client_account$', ClientAccountHandler),
    verfication_route,     
], config=config.WSGI_CONFIG, debug=config.DEBUG)         
    
    