"""
Define the various classes for RequestHandler
"""

import webapp2
import json
import logging
import os.path

from webapp2_extras import auth
from webapp2_extras import sessions

import config
from config import JINJA_ENV, DEBUG
from model.base_model import FormField
from model.account import UserRole, AuditLog
from google.appengine.api import mail
from utils.handler_utils import *



"""
Base class for all the handlers used in the system
"""

#from handler.auth import verfication_route

class BaseHandler(webapp2.RequestHandler):
    
    @webapp2.cached_property
    def min_access_level(self):
        return 0
    
    @webapp2.cached_property
    def max_access_level(self):
        return 1000
    
    def __init__(self, request, response):
        #Set self.request, self.response and self.app
        self.initialize(request, response)
                        
        #Add google analytics tracking.
        #ga_tracking.track_event_to_ga(request.path, "Get", "View", "100")
    
    @webapp2.cached_property
    def auth(self):
        """Shortcut to access the auth instance as a property."""
        return auth.get_auth()
    
    @webapp2.cached_property
    def user_info(self):
        """Shortcut to access a subset of the user attributes that are stored
        in the session.

        The list of attributes to store in the session is specified in
          config['webapp2_extras.auth']['user_attributes'].
        :returns
          A dictionary with most user information
        """
        return self.auth.get_user_by_session()
    
    @webapp2.cached_property
    def user(self):
        """Shortcut to access the current logged in user.
        Unlike user_info, it fetches information from the persistence layer and
        returns an instance of the underlying model.
        :returns
        The instance of the user model associated to the logged in user.
        """
        u = self.user_info
        return self.user_model.get_by_id(u['user_id']) if u else None

    @webapp2.cached_property
    def user_model(self):
        """Returns the implementation of the user model.
        It is consistent with config['webapp2_extras.auth']['user_model'], if set.
        """
        return self.auth.store.user_model
        
    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(backend="datastore")
    
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)       
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
                    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        #Key for OneMap API Javascript
        if not params:
            params = {}
        
        params['onemap_key'] = config.ONEMAP_KEY
        params['user'] = self.user_info

        #if config.DEBUG:
            #logging.info("One Map Key [parma]: %s" %params['onemap_key'])

        t = JINJA_ENV.get_template(template)
        return t.render(params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))
        
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)
        
    def async_render_msg(self, result, redirect_addr=None):
        response = {}
        response['status'] = result['status']
        
        if result['message']:
            result['message'] = result['message'].replace('_', " ")
            result['message'] = result['message'].capitalize()
        
        response['message'] = result['message']
        
        if redirect_addr:
            response['redirect'] = redirect_addr
        self.render_json(response)
        
    def get_domain(self):
        return self.request.host
    
    def send_email(self, to_address, subject, msg):
        sender = "admin@"+config.APP_ID+".appspotmail.com"
        message = mail.EmailMessage(sender=sender, subject=subject)
        
        message.to = to_address
        message.body = msg
        message.bcc = config.ADMIN_ALERT_EMAIL
        
        logging.info('sent by %s' %(sender))
        #mail.send_mail(sender, to_address, subject, msg)
        message.send()    

class CRUDHandler(BaseHandler):
    @user_required
    def __init__(self, *arg, **kwargs):
        super(CRUDHandler, self).__init__(*arg, **kwargs)
        self.form = {}
        self.form_funcs = {}
        self.model_cls = None
        self.page_name = None
        self.form['tb_buttons'] = None
       
        #property that define if the value is included in table
        self.table_include_list = None
        self.table_exclude_list = None
        
        #property that define if the value is included in the initial form 
        self.form_include_list = None
        self.form_exclude_list = None
        
        #property that define if the value is included in the create action
        self.create_include_list = None
        self.create_exclude_list = None
        
        #property that define if the value is included for edit action
        self.edit_include_list = None
        self.edit_exclude_list = None  
        
        #property that define if the field is a repeat field
        self.repeat_field_list = None
        
        #property that define the template search list
        self.template_upload_set_list = None
        
        #property that define the template for the form
        self.default_form = None
        
        
        #property that determine if the even logged into audit
        self.is_audit = False
        self.audit_event_key = None

        #property that define the audit action
        self.audit_event_list= ['Create', 'Edit', 'Delete']        
        
        #Customize page information
        self.init_form_data()
        
        self.form['create_id'] = 'create_form'
        self.form['create_type'] = 'async_create'
        self.form['edit_id'] = 'edit_form'
        self.form['edit_type'] = 'async_edit'
        self.form['upload_id'] = 'upload_form'
        self.form['upload_type'] = 'async_upload'

        if self.page_name:
            if 'header' not in self.form:
                self.form['header'] = ('Manage %s' %(self.page_name)).title()
                self.form['create_title'] = ('Create New %s' %(self.page_name)).title()
                self.form['upload_title'] = ('Upload  %s' %(self.page_name)).title()
                self.form['edit_title'] = ('Edit  %s' %(self.page_name)).title()
        
        if not self.form['tb_buttons']:
            self.form['tb_buttons'] = 'create,edit,delete,export,import'
        
        self.form_funcs['async_create'] = self.async_create 
        self.form_funcs['async_edit'] = self.async_edit
        self.form_funcs['async_delete'] = self.async_delete
        self.form_funcs['async_activate'] = self.async_activate
        self.form_funcs['async_upload'] = self.async_upload
        self.form_funcs['async_query_all_json'] = self.async_query_all_json
        self.form_funcs['async_query_kind'] = self.async_query_kind
        self.form_funcs['ajax_search'] = self.ajax_search
        self.form_funcs['template_search'] = self.template_search
        
        if not self.default_form:
            self.default_form = "crud_form.html"

    def create_audit_log(self, action, rec_entity):
        if self.is_audit == True and action in self.audit_event_list:
            if self.audit_event_key:
                key_id = getattr(rec_entity, self.audit_event_key)
                event_desc = "%s %s '%s'" %(action, self.page_name, key_id)
            else:
                event_desc = "%s %s" %(action, self.page_name)
        
            new_log = {}
            new_log['email_created'] = "%s (%s)" %(self.user.email_lower,
                                                   self.user.user_role.get().role_name)
            new_log['location_created'] = get_current_location()
            new_log['event_desc'] = event_desc
            new_log['business_group'] = self.user.business_group
            new_log['user_created'] = self.user.key
            new_log['business_team'] = self.user.business_team
            
            result = AuditLog.create_model_entity(model_rec=new_log, 
                                                    user_business_group=self.user.business_group,
                                                    user_business_team=self.user.business_team)
            
    def init_form_data(self):
        pass
    
    def process_get_form_data(self, form_data):
        return form_data    
        
    def get(self):
        self.form['field_list'] = self.model_cls.get_form_fields(
                                    self.form_include_list, 
                                    self.form_exclude_list,
                                    user_business_group=self.user.business_group,
                                    user_business_team=self.user.business_team
                                    )
        self.form = self.process_get_form_data(self.form)
        self.render(self.default_form, form=self.form)
        
    def get_edit(self, model_entity, edit_attr_list=None):
        self.form['field_list'] = self.model_cls.get_form_fields(
                                    self.edit_include_list, 
                                    self.edit_exclude_list,
                                    user_business_group=self.user.business_group,
                                    user_business_team=self.user.business_team)
        tmp_obj = model_entity.to_dict()
        for field in self.form['field_list']:
            prop_name = field['prop_name']
            field['default_value'] = tmp_obj[prop_name]
            if edit_attr_list and prop_name in edit_attr_list:
                field['edit_attr'] += " " + edit_attr_list[prop_name]
        
        #print ("form:%s" %self.form)
        self.render("update_form.html", form=self.form)

    def post(self):
        form_action = self.request.get("formType")
        self.form_funcs[form_action]()
    
    def process_create_data(self, model_rec):
        return model_rec
    
    def post_create_process(self, result, model_rec):
        return result
     
    def async_create(self):
        post_dict = {}
        model_rec = self.process_create_data(self.request.POST)
        
        for key in model_rec:
            if self.create_include_list and key not in self.create_include_list:
                continue
            
            if self.create_exclude_list and key in self.create_exclude_list:
                continue
            
            if self.repeat_field_list and key in self.repeat_field_list:
                post_dict[key] = model_rec.getall(key)
            else:
                post_dict[key] = model_rec.get(key)                
            
        result = self.model_cls.create_model_entity(model_rec=post_dict, 
                                                    user_business_group=self.user.business_group,
                                                    user_business_team=self.user.business_team)
        result = self.post_create_process(result=result, model_rec=post_dict)
        if result['status'] == True:
            rec_entity = result['entity']
            self.create_audit_log('Create', rec_entity)
        else:
            logging.error(result['message'])
        self.async_render_msg(result)


    def process_edit_data(self, model_rec):
         return model_rec
            
    def async_edit(self):
        post_dict = {}
        model_rec = self.process_edit_data(self.request.POST)
                
        for key in model_rec:
            if self.edit_include_list and key not in self.edit_include_list:
                continue
            
            if self.edit_exclude_list and key in self.edit_exclude_list:
                continue
            
            if self.repeat_field_list and key in self.repeat_field_list:
                post_dict[key] = model_rec.getall(key)
            else:
                post_dict[key] = model_rec.get(key)
                
        result = self.model_cls.update_model_entity(post_dict, 
                                                    user_business_group=self.user.business_group,
                                                    user_business_team=self.user.business_team)
        if result['status'] == True:        
            rec_entity = result['entity']
            self.create_audit_log('Edit', rec_entity)
        else:
            logging.error(result['message'])
        
        self.async_render_msg(result)

    def process_upload_data(self, upload_data):
        return upload_data
    
    def set_template_value(self, template_prop_name, 
                           upload_data_rec):
        #print "upload_data_rec:%s" %upload_data_rec
        #Get the template_id
        if template_prop_name in upload_data_rec:
            template_name = upload_data_rec[template_prop_name]
        else:
            return
        
        if template_name:
            result = self.model_cls.convert_keyprop_by_value(
                                                             template_prop_name, 
                                                             template_name,
                                                             user_business_group=self.user.business_group,
                                                             user_business_team=self.user.business_team)
            if result['status'] == False:
                return result
            else: 
                template_key = result['key']
                del result['key']        
        
        template_rec = template_key.get().to_dict() 
        for key in self.template_upload_set_list:
            if key in upload_data_rec:
                if upload_data_rec[key].strip() =="":
                    upload_data_rec[key] = template_rec[key]
            else:
                upload_data_rec[key] = template_rec[key]
        return upload_data_rec
        
    def async_upload(self):
        upload_data = json.loads(self.request.get('upload_data'))
        upload_data = self.process_upload_data(upload_data)
        #for return value, keep the json format
        return_data = json.loads(self.request.get('upload_data'))

        success_cnt = 0
        fail_cnt = 0
        success_message = ""
        fail_message = ""
        
        for idx in range(0, len(upload_data)):
            each = upload_data[idx]
            each_down = return_data[idx]
            if each:
                result = self.model_cls.create_model_entity(model_rec=each, 
                                                            user_business_group=self.user.business_group,
                                                            type='upload',
                                                            user_business_team=self.user.business_team)
                
                each_down['upload_status'] = result['status']
                each_down['status_message'] = result['message']
                each_down['_entity_id'] = None
                if result['status'] == True:
                    success_cnt +=1
                    success_message = result['message']
                    rec_entity = result['entity']
                    self.create_audit_log('Create', rec_entity)
                    
                else:
                    fail_cnt +=1
                    fail_message =  result['message']
                    logging.error(result['message'])
                    
                
        result = construct_return_msg(success_cnt, fail_cnt, "upload", success_message, fail_message);
        result['upload_return_data'] = return_data
        result['success_cnt'] = success_cnt
        result['fail_cnt'] = fail_cnt
        #self.async_render_msg(result)
        self.render_json(result)
        
    def async_delete(self):
        del_data = json.loads(self.request.get('del_data'))
        success_cnt = 0
        fail_cnt = 0
        success_message = ""
        fail_message = ""
        result = {}
        for each in del_data:
            result = self.model_cls.delete_model_entity(each)
            #print ("result %s" %result)
            if result['status'] == True:
                success_cnt +=1
                success_message = result['message']
                rec_entity = result['entity']
                self.create_audit_log('Delete', rec_entity)
            else:
                fail_cnt +=1
                fail_message =  result['message']
                logging.error(result['message'])
                    
        result = construct_return_msg(success_cnt, fail_cnt, "delete", success_message, fail_message);
        self.async_render_msg(result)
            
        #status, msg = self.model_cls.del_model_entity(self.request, self.number_id)
        #self.async_render_msg(status, msg)
        
    def post_activate_process(self, result, model_rec):
        return result
        
    def async_activate(self):
        act_data = json.loads(self.request.get('act_data'))
        success_cnt = 0
        fail_cnt = 0
        success_message = ""
        fail_message = ""
        result = {}
        for each in act_data:
            act_dict = {}
            act_dict['_entity_id'] = each['_entity_id']
            act_dict['status'] = config.ACTIVE_STATUS
            result = self.model_cls.update_model_entity(act_dict, 
                                                        user_business_group=self.user.business_group,
                                                        user_business_team=self.user.business_team)
            #print ("result %s" %result)
            if result['status'] == True:
                success_cnt +=1
                success_message = result['message']
                rec_entity = result['entity']
                self.create_audit_log('Activate', rec_entity)
                result = self.post_activate_process(result, act_dict)
            else:
                fail_cnt +=1
                fail_message =  result['message']
                logging.error(result['message'])
                    
        result = construct_return_msg(success_cnt, fail_cnt, "activate", success_message, fail_message);
        self.async_render_msg(result)        

    def async_query_kind(self):
        kind_name = self.request.get('kind_name')
        data_list = FormField.query_kind_dict(kind_name)
        result_list = []
        
        for each in data_list:
            prop_name = each['prop_name']
            
            if self.table_include_list and prop_name not in self.table_include_list:
                continue
            
            if self.table_exclude_list and prop_name in self.table_exclude_list:
                continue
            
            result_list.append(each)
            
        self.render_json(result_list)        
        
    def async_query_all_json(self, 
                             cond_list=None, 
                             order_list=None, 
                             is_with_entity_id=True,
                             user_business_group=None,
                             user_business_team=None):
        data ={}
        data['data'] = self.model_cls.query_data_to_dict(cond_list=cond_list, 
                                                         order_list=order_list,
                                                         is_with_entity_id=is_with_entity_id,
                                                         user_business_group=user_business_group,
                                                         user_business_team=user_business_team)
        self.render_json(data)
        
    def ajax_search(self):
        record = self.process_ajax_search()
        self.render_json(record)
        
    def process_ajax_search(self):
        return None
    
    def template_search(self):
        record = self.process_template_search()
        self.render_json(record)
        
    def process_template_search(self):
        return None
    
