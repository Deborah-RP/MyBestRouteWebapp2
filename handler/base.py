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
from model.account import UserRole

#from utils import ga_tracking

from utils.ndb_utils import *
from utils.handler_utils import *

"""
Base class for all the handlers used in the system
"""

#from handler.auth import verfication_route

class BaseHandler(webapp2.RequestHandler):
    
    @webapp2.cached_property
    def access_level(self):
        return 0
    
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
        
    def async_render_msg(self, status, msg, redirect_addr=None):
        return_val = {}
        return_val['status'] = status
        if msg:
            msg = msg.replace('_', " ")
            return_val['msg'] = msg.capitalize()
        
        if redirect_addr:
            return_val['redirect'] = redirect_addr
        self.render_json(return_val)        
  
class CRUDHandler(BaseHandler):
    @user_required
    def __init__(self, *arg, **kwargs):
        super(CRUDHandler, self).__init__(*arg, **kwargs)
        self.form = {}
        self.form['create_id'] = 'create_form'
        self.form['create_type'] = 'async_create'
        self.form['edit_id'] = 'edit_form'
        self.form['edit_type'] = 'async_edit'
        self.form['upload_id'] = 'upload_form'
        self.form['upload_type'] = 'async_upload'
        self.form['header'] = ('Manage %s' %(self.page_name)).title()
        self.form['create_title'] = ('Create New %s' %(self.page_name)).title()
        self.form['upload_title'] = ('Upload  %s' %(self.page_name)).title()
        self.form['edit_title'] = ('Edit  %s' %(self.page_name)).title()
        self.form['tb_buttons'] = 'create,edit,delete,export,import'
        
        self.form_funcs = {}
        self.form_funcs['async_create'] = self.async_create 
        self.form_funcs['async_edit'] = self.async_edit
        self.form_funcs['async_delete'] = self.async_delete
        self.form_funcs['async_upload'] = self.async_upload
        self.form_funcs['async_query_all_json'] = self.async_query_all_json
        self.form_funcs['async_query_kind'] = self.async_query_kind
        
        self.model_cls = None
        self.number_id = False
        
        self.table_include_list = None
        self.table_exclude_list = None
        self.form_include_list = None
        self.form_exclude_list = None
        self.create_include_list = None
        self.create_exclude_list = None
        self.edit_include_list = None
        self.edit_exclude_list = None
        
    def get(self):	
        self.form['field_list'] = self.model_cls.get_form_fields(self.form_include_list, self.form_exclude_list)
        self.render("crud_form.html", form=self.form)
        
    def get_edit(self, model_entity):
        self.form['field_list'] = self.model_cls.get_form_fields(self.edit_include_list, self.edit_exclude_list)
        tmp_obj = model_entity.entity_to_dict()
        for field in self.form['field_list']:
            prop_name = field['prop_name']
            field['value'] = tmp_obj[prop_name]
        self.render("update_form.html", form=self.form)

    def post(self):
        form_action = self.request.get("formType")
        self.form_funcs[form_action]()
        
    def async_create(self):
        post_dict = {}
        for key in self.request.POST:
            if self.create_include_list and key not in self.create_include_list:
                continue
            
            if self.create_exclude_list and key in self.create_exclude_list:
                continue
            
            post_dict[key] = self.request.POST[key]
        status, msg = self.model_cls.create_model_entity(post_dict)
        self.async_render_msg(status, msg)
        
    def async_edit(self):
        post_dict = {}
        for key in self.request.POST:
            if self.edit_include_list and key not in self.edit_include_list:
                continue
            
            if self.edit_exclude_list and key in self.edit_exclude_list:
                continue
            
            post_dict[key] = self.request.POST[key]
        status, msg = self.model_cls.update_model_entity(post_dict, self.number_id)
        self.async_render_msg(status, msg)
        
    def async_upload(self):
        upload_data = json.loads(self.request.get('upload_data'))
        success_cnt = 0
        fail_cnt = 0
        msg = ""
        print("upload_data %s len is %s" %(upload_data, len(upload_data)))
        for each in upload_data:
            if each:
                status, msg = self.model_cls.create_model_entity(each)
                if status:
                    success_cnt +=1
                else:
                    fail_cnt +=1
                
        status, msg = construct_return_msg(success_cnt, fail_cnt, "upload", msg);
        self.async_render_msg(status, msg)
        
    def async_delete(self):
        del_data = json.loads(self.request.get('del_data'))
            
        success_cnt = 0
        fail_cnt = 0
        
        for each in del_data:
            status, msg = self.model_cls.del_model_entity(each, self.number_id)
            if status:
                success_cnt +=1
            else:
                fail_cnt +=1
        status, msg = construct_return_msg(success_cnt, fail_cnt, "delete", msg);
        self.async_render_msg(status, msg)
            
        #status, msg = self.model_cls.del_model_entity(self.request, self.number_id)
        #self.async_render_msg(status, msg)

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
        
    def async_query_all_json(self, cond_list=None):
        data ={}
        data['data'] = self.model_cls.query_all_dict(cond_list)
        self.render_json(data)