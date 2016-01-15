import logging
import webapp2

import config
from model.account import User, PricePlan, BusinessGroup, AuditLog
from handler.auth import verfication_route
from handler.role_access import UserHandler, SysAdminHandler

class PricePlanHandler(SysAdminHandler):
    def init_form_data(self):
        self.repeat_field_list = ['plan_modules']
        self.page_name = 'price plan'
        self.form['action'] = '/sys_admin/price_plan'
        self.form['dt_source'] = 'PricePlan'
        self.is_audit = True
        self.audit_event_key = 'plan_name'
        self.model_cls = PricePlan  
       
class BusinessGroupHandler(SysAdminHandler):
    def init_form_data(self):
        self.page_name = 'business group'
        self.form['action'] = '/sys_admin/business_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.is_audit = True
        self.audit_event_key = 'business_name'        
        self.model_cls = BusinessGroup
        
class ActivateGroupHandler(SysAdminHandler):
    def init_form_data(self):
        self.page_name = 'business group'
        self.form['header'] = 'Activate Business Group'
        self.form['action'] = '/sys_admin/activate_group'
        self.form['dt_source'] = 'BusinessGroup'
        self.is_audit = True
        self.audit_event_key = 'business_name'
        self.audit_event_list= ['Activate']    
        self.model_cls = BusinessGroup
        self.form['tb_buttons'] = 'activate,export'
    
    def async_query_all_json(self):
        cond_list = [BusinessGroup.status == config.PENDING_STATUS]
        SysAdminHandler.async_query_all_json(self, 
                                             cond_list=cond_list, 
                                             cur_user=self.user)

    def post_activate_process(self, result, model_rec):
        if result['status'] == True:
            business_group = result['entity']
            to_address= self.get_admin_emails(business_group.key)
            if len(to_address) > 0:
                self.send_activation_email(business_group.business_name, to_address)
            else:
                logging.info('No group admin found')
        return result
    
    def get_admin_emails(self, business_group):
        cond_list = [User.business_group == business_group,
                     User.access_level == config.GROUP_ADMIN.access_level]
        result = User.query_data_to_dict(cur_user=self.user,
                                         cond_list=cond_list)
        #logging.debug(result)
        to_address = ""
        for each in result:
            #logging.debug(each)
            if len(to_address) > 0:
                to_address += ';'+each['email_lower']
            else:
                to_address = each['email_lower']
                
        return to_address
        
    def send_activation_email(self, group_name, to_address):
        subject = "Your group account has been activated"
        msg = ("""
        Dear %s admin:
        
        Your registered group account has been activated. 
        
        You can now visit %s to verify your account and sign in to access the website.
        
        The Route Planner Team
    
    """ %(group_name, self.request.host))
        logging.info("Activation email sent to %s: %s" %(to_address, msg))
        self.send_email(to_address, subject, msg)
        
class AuditLogHandler(SysAdminHandler):
    def init_form_data(self):
        self.page_name = 'audit log'
        self.form['action'] = '/sys_admin/audit_log'
        self.form['dt_source'] = 'AuditLog'
        self.model_cls = AuditLog 
        self.form['tb_buttons'] = 'export'
    
    def async_query_all_json(self):
        super(AuditLogHandler, self).async_query_all_json()
        
class SysAdminUserHandler(SysAdminHandler, UserHandler):
    def init_form_data(self):
        self.page_name = 'user'
        self.form['action'] = '/sys_admin/users'
        self.form['dt_source'] = 'User'
        self.model_cls = User
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.max_user_level = config.SYS_ADMIN.access_level
        self.min_user_level = config.GROUP_ADMIN.access_level
        self.is_audit = True
        self.audit_event_key = 'email_lower'        
        self.create_exclude_list = ['business_team']
        self.edit_exclude_list = ['business_team']
        self.form_exclude_list = ['business_team']
            
app = webapp2.WSGIApplication([
    (r'/sys_admin/price_plan$', PricePlanHandler),
    (r'/sys_admin/business_group$', BusinessGroupHandler),
    (r'/sys_admin/activate_group', ActivateGroupHandler),
    (r'/sys_admin/audit_log$', AuditLogHandler),
    (r'/sys_admin/users$', SysAdminUserHandler),
    verfication_route,
], config=config.WSGI_CONFIG, debug=config.DEBUG)