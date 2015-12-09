import logging
import webapp2

from utils.handler_utils import *

from handler.team import TeamHandler
from model.account import *
from model.plan import *
from model.base_doc import *
import config

class TeamUserHandler(TeamHandler):
    @webapp2.cached_property
    def min_access_level(self):
        user_role = UserRole.query(UserRole.role_name == config.TEAM_USER).get()
        return user_role.access_level
    
class TaskHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Task'
        self.form['action'] = '/team_user/task'
        self.form['dt_source'] = 'Task'
        self.repeat_field_list = ['required_skills']
        self.model_cls = Task
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'postal'
        self.form['ajax_search_set_fields'] = ''
        self.form['create_warning'] = "Task with the same ID will replace the existing one!"
        self.default_form = 'crud_ba_form.html'  
        
    def process_ajax_search(self):
        postal = self.request.get('postal').strip()
        if postal != "":
            address_record = SGPostal.get_record_dict(postal)
            if not address_record:
                record = {}
                record['ajax_search_message'] = '%s address postal code not found in Singapore Postal Index!' %postal
                return record
        return None
    
    def process_address(self, model_rec):
        postal = model_rec.get('postal').strip()
        business_group = self.user.business_group
        user_created = self.user.key                
        business_team = self.user.business_team
        address_entity = Address.create_from_sgpostal(postal, 
                                                      business_group, 
                                                      user_created,
                                                      business_team)
        model_rec['postal'] = address_entity.key
        task_latlng = address_entity.latlng
        model_rec['task_latlng'] = "%s, %s" %(task_latlng.lat, task_latlng.lon)
        return model_rec
    
    def process_create_data(self, model_rec):
        return self.process_address(model_rec)  
    
    def process_edit_data(self, model_rec):
        return self.process_address(model_rec)
    
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each = self.process_address(each)
        return super(TaskHandler, self).process_upload_data(upload_data) 
    
class RoutePlanHandler(TeamUserHandler): 
    def init_form_data(self):
        self.page_name = 'Route Plan'
        self.form['action'] = '/team_user/route_plan'
        self.form['dt_source'] = 'RoutePlan'
        self.repeat_field_list = ['driver_set', 'task_set']
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.form['upload_task_create_warning'] = "Task with the same ID will replace the existing one!"
        self.model_cls = RoutePlan
        
    def get(self):
        self.form['field_list'] = self.model_cls.get_form_fields(
                                    self.form_include_list, 
                                    self.form_exclude_list,
                                    self.user.business_group,
                                    self.user.business_team)
        self.form['route_task_field_list'] = Task.get_form_fields(
                                    self.form_include_list, 
                                    self.form_exclude_list,
                                    self.user.business_group,
                                    self.user.business_team)
        self.render("plan_crud_form.html", form=self.form)
        
    
    def post_create_process(self, result, model_rec):
        if result['status'] == False:
            return result
        
        #Optimize the 
        if model_rec['submit_and_optimized'] == "Yes":
            if model_rec['optimized_algo'] == 'Ortec':
                print ("Optimized with Ortec!")
        
        return result
    
    
    def async_upload(self):
        return   
    
class UserProfileHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'User Profile'
        self.form['action'] = '/team_user/user_profile'
        self.form['dt_source'] = 'User'
        self.model_cls = User 
        self.edit_include_list = ['_entity_id', 'email', 'user_name', 'created', 'last_login_time']
        
    def get(self):
        model_entity = self.user
        self.get_edit(model_entity)
        
    def async_edit(self):
        self.request.POST['user_access_level'] = self.user.access_level
        super(UserProfileHandler, self).async_edit()         
        
class ChangePasswordHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Password'
        self.form['action'] = '/team_user/change_password'
        
    def get(self):
        self.render('change_password.html', form=self.form)
        
    def post(self):
        password = self.request.get('password')
        if not password or password != self.request.get('confirm_password'):
            self.async_render_msg(False, "Password does not match!")
            return
        self.user.set_password(password)
        self.user.put()
        response = {}
        response['status'] = True
        response['message'] = "Your password has been changed!"
        self.async_render_msg(response)

app = webapp2.WSGIApplication([
    (r'/team_user/user_profile$', UserProfileHandler),
    (r'/team_user/change_password$', ChangePasswordHandler),
    (r'/team_user/task$', TaskHandler),
    (r'/team_user/route_plan$', RoutePlanHandler),    
], config=config.WSGI_CONFIG, debug=config.DEBUG)         
    