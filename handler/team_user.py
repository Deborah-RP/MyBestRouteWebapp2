import logging
import webapp2

from utils.handler_utils import *

from handler.role_access import TeamHandler, TeamTemplateHandler
from model.account import *
from model.plan import *
from model.base_doc import *
from random import randint
import config

class TeamUserHandler(TeamTemplateHandler):
    @webapp2.cached_property
    def min_access_level(self):
        user_role = UserRole.query(UserRole.role_name == config.TEAM_USER.role_name).get()
        return user_role.access_level
    
class AreaHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Area'
        self.form['action'] = '/team_user/set/area'
        self.form['dt_source'] = 'Area'
        self.model_cls = Area
        self.is_audit = True
        self.audit_event_key = 'area_name'   
        
class AddressHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Address'
        self.form['action'] = '/team_user/set/address'
        self.form['dt_source'] = 'Address'
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['ajax_search_set_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.is_audit = True
        self.audit_event_key = 'cust_name' 
        self.model_cls = Address

    def process_get_form_data(self, form_data):
        form_data = TeamHandler.process_get_form_data(self, form_data)
        return self.set_default_country(form_data)
        
    def process_ajax_search(self):
        result = {}
        if (self.request.get('country') == ""):
            result['ajax_search_message'] = 'Please select a country!'
            return result
        #cond_list = self.prepare_cond_list()
        record = AddressDocument.get_address_doc_record(self.request)
        result['data'] = record
        if record and len(record) > 1:
            result['ajax_search_message'] = 'Multiple addresses found!'
        elif record == None:
            result['ajax_search_message'] = 'No address found!'
        return result
    
    def process_address_data(self, model_rec):
        record = AddressDocument.get_address_doc_record(model_rec)
        if record and len(record)>0:
            #Get the first record
            
            model_rec = Address.get_format_address(model_rec, record[0])
            for key in record[0]:
                if key in model_rec and model_rec[key] != "":
                    #Don't change the original value if exist
                    continue
                else:
                    model_rec[key] = record[0][key]
        return model_rec

    def process_create_data(self, model_rec):
        model_rec = self.process_address_data(model_rec)
        return TeamUserHandler.process_create_data(self, model_rec)
    
    def process_edit_data(self, model_rec):
        model_rec = self.process_address_data(model_rec)
        return TeamUserHandler.process_edit_data(self, model_rec)
    
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each = self.process_address_data(each)
        return super(AddressHandler, self).process_upload_data(upload_data)
    
class DepotHandler(AddressHandler):
    def init_form_data(self):
        self.page_name = 'Depot Station'
        self.form['action'] = '/team_user/set/depot'
        self.form['dt_source'] = 'Depot'
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'depot_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['ajax_search_set_fields'] = 'depot_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'depot_template'
        self.form['template_search_set_fields'] = 'loading_duration,unloading_duration'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")      
        self.model_cls = Depot
        self.default_form = 'crud_ba_form.html'
        self.is_audit = True
        self.audit_event_key = 'depot_name' 
        
class DepotTemplateHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Depot Station Template'
        self.form['action'] = '/team_user/set/depot_template'
        self.form['dt_source'] = 'DepotTemplate'
        self.model_cls = DepotTemplate
        self.is_audit = True
        self.audit_event_key = 'template_name' 

class VehicleTypeHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Type of Vehicle'
        self.repeat_field_list = ['max_capacities']
        self.form['action'] = '/team_user/set/vehicle_type'
        self.form['dt_source'] = 'VehicleType'
        self.model_cls = VehicleType
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'vehicle_type_template'
        self.form['template_search_set_fields'] = 'max_capacities,max_num_order,max_distance,oil_cost_per_km,fixed_cost'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")
        self.default_form = 'crud_ba_form.html'
        self.is_audit = True
        self.audit_event_key = 'type_name'               
        
class VehicleTypeTemplateHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Vehicle Type Template'
        self.form['action'] = '/team_user/set/vehicle_type_template'
        self.form['dt_source'] = 'VehicleTypeTemplate'
        self.repeat_field_list = ['max_capacities']
        self.model_cls = VehicleTypeTemplate
        self.is_audit = True
        self.audit_event_key = 'template_name' 
        
class DriverTemplateHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Driver Template'
        self.form['action'] = '/team_user/set/driver_template'
        self.form['dt_source'] = 'DriverTemplate'
        self.repeat_field_list = ['skills']
        '''
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'start_address,end_address'
        self.form['ajax_search_set_fields'] = ''
        '''
        self.model_cls = DriverTemplate
        self.is_audit = True
        self.audit_event_key = 'template_name'        
    
    '''
    def process_ajax_search(self):
        address_list = {}
        address_list['Start'] = self.request.get('start_address').strip()
        address_list['End'] = self.request.get('end_address').strip()
        for address_id in address_list:
            postal = address_list[address_id]
            if postal != "":
                address_record = SGPostal.get_record_dict(postal)
                if not address_record:
                    record = {}
                    record['ajax_search_message'] = '%s address postal code not found in Singapore Postal Index!' %address_id
                    return record
        return None
    '''
    
    '''
    def process_address(self, model_rec):
        address_list = {}
        address_list['start_address'] = model_rec.get('start_address').strip()
        address_list['end_address'] = model_rec.get('end_address').strip()
            
        for address_id in address_list:
            postal = address_list[address_id]
            business_group = self.user.business_group
            user_created = self.user.key
            business_team = self.user.business_team                
            address_entity = Address.create_from_sgpostal(postal, 
                                                          business_group, 
                                                          user_created,
                                                          business_team)
            model_rec[address_id] = address_entity.key
        return model_rec
    '''
    
    '''
    def process_create_data(self, model_rec):
        return self.process_address(model_rec)
    '''  
    
    '''
    def process_edit_data(self, model_rec):
        return self.process_address(model_rec)
    '''
    
class DriverHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Driver'
        self.form['action'] = '/team_user/set/driver'
        self.form['dt_source'] = 'Driver'
        self.repeat_field_list = ['skills']
        self.model_cls = Driver
        ''''
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'start_address,end_address'
        self.form['ajax_search_set_fields'] = ''
        '''        
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'driver_template'
        self.form['template_search_set_fields'] = 'vehicle_info,served_area,start_address,end_address,speed_factor,work_start_time,work_end_time,max_work_hour,break_start_time,break_end_time,break_duration,skills,cost_per_hour,overwork_rate_per_hour'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")
        self.default_form = 'crud_ba_form.html'
        self.is_audit = True
        self.audit_event_key = 'driver_name'
        
    def process_create_data(self, model_rec):
        model_rec['driver_pin'] = ''.join(["%s" % randint(0, 9) for num in range(0, 4)])
        return TeamTemplateHandler.process_create_data(self, model_rec)
    
    
class PlanTaskHandler(TeamUserHandler):
    def init_form_data(self):
        self.page_name = 'Task'
        self.form['action'] = '/team_user/plan/task'
        self.form['dt_source'] = 'Task'
        self.repeat_field_list = ['required_skills']
        self.model_cls = Task
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['ajax_search_set_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['create_warning'] = "Task with the same ID will replace the existing one!"
        self.form_exclude_list = ['epod', 'sms_log', 'call_log', 'planned_time', 
                                  'planned_datetime','estimated_datetime', 
                                  'finalized_datetime', 'finalized_location', 'fail_count', 
                                  'partial_count', 'task_status', 'remarks']
        self.table_exclude_list = self.form_exclude_list
        self.default_form = 'crud_ba_form.html'  
        self.is_audit = True
        self.audit_event_key = 'task_id'
        self.task_status_default = 'Unplanned'
        
        
    def process_get_form_data(self, form_data):
        form_data = TeamHandler.process_get_form_data(self, form_data)
        return self.set_default_country(form_data) 
    
    def process_address_data(self, model_rec, op_type=None):
        cond_list = self.prepare_cond_list()
        model_rec = Address.set_geolocation(model_rec=model_rec, 
                                            cond_list=cond_list, 
                                            cur_user=self.user,
                                            op_type=op_type)
        return model_rec
    
    def process_task_data(self, model_rec, op_type=None):
        model_rec['task_status'] = self.task_status_default
        model_rec = self.process_address_data(model_rec, op_type)
        return model_rec
        
        
    def process_create_data(self, model_rec):
        return self.process_task_data(model_rec)
    
    def process_edit_data(self, model_rec):
        return self.process_task_data(model_rec)    
    
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each = self.process_task_data(each, op_type='upload')
            '''for key in record:
                if key in self.form['ajax_search_set_fields'] and key not in each:
                    each[key] = record[key]
            '''
        return super(PlanTaskHandler, self).process_upload_data(upload_data)
    
    def async_query_all_json(self, 
                             cond_list=None, 
                             order_list=None, 
                             is_with_entity_id=True, 
                             cur_user=None):
        
        if cond_list != None:
            cond_list.append(Task.task_status == self.task_status_default)
        else:
            cond_list = [Task.task_status == self.task_status_default]
        logging.info(cond_list)
        return super(PlanTaskHandler, self).async_query_all_json(cond_list=cond_list, 
                                                                 order_list=order_list, 
                                                                 is_with_entity_id=is_with_entity_id, 
                                                                 cur_user=cur_user)
    
    def process_ajax_search(self):
        result = {}
        if (self.request.get('country') == ""):
            result['ajax_search_message'] = 'Please select a country!'
            return result
        cond_list = self.prepare_cond_list()
        record = Address.search_address_record(model_rec=self.request,
                                               cond_list=cond_list,
                                               cur_user=self.user)
        result['data'] = record
        if record and len(record) > 1:
            logging.info(record)
            result['ajax_search_message'] = 'Multiple addresses found!'
        elif record == None:
            result['ajax_search_message'] = 'No address found!'
        return result
    
class TrackTaskHandler(PlanTaskHandler):
    def init_form_data(self):
        self.page_name = 'Task'
        self.form['action'] = '/team_user/track/task'
        self.form['dt_source'] = 'Task'
        self.repeat_field_list = ['required_skills', 'cust_emails', 'cust_phones']
        self.model_cls = Task
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['ajax_search_set_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['create_warning'] = "Task with the same ID will replace the existing one!"
        self.form['planned_date_range']= True
        self.form['user_channel'] = True
        self.form_exclude_list = ['epod', 'sms_log', 'call_log', 'time_window_from', 'time_window_to', 
                                  'planned_datetime','estimated_datetime', 
                                  'finalized_datetime', 'finalized_location', 'fail_count', 
                                  'partial_count', 'task_status', 'remarks']
        self.table_exclude_list = ['time_window_from', 'time_window_to']
        self.default_form = 'crud_ba_form.html'  
        self.is_audit = True
        self.audit_event_key = 'task_id'
        self.task_status_default = 'Pending'
        
    def async_query_all_json(self, 
                             cond_list=None, 
                             order_list=None, 
                             is_with_entity_id=True, 
                             cur_user=None):
        
        if cond_list != None:
            cond_list = cond_list + [Task.task_status.IN(['Pending', 'Ongoing', 'Finalized', 'Partial', 'Lapsed', 'Failed'])]
        else:
            cond_list = [Task.task_status.IN(['Pending', 'Ongoing', 'Finalized', 'Partial', 'Lapsed', 'Failed'])]
            
        #logging.info(cond_list)
        return TeamHandler.async_query_all_json(self,
                                                cond_list=cond_list, 
                                                order_list=order_list, 
                                                is_with_entity_id=is_with_entity_id, 
                                                cur_user=cur_user)
        

    def post_query_all_json(self, data):
        tasks = data['data']
        for task in tasks:
            if task['task_status'] != 'Pending':
                task['DT_RowClass'] = 'noselect ' + task['task_status']
            else:
                task['DT_RowClass'] = task['task_status']
                
        #Test only
        received_users = [self.user]
        received_groups = [self.user.business_group.get()]
        received_teams = BusinessTeam.query(BusinessTeam.team_name == 'Test Team 01-02').fetch()
        received_pages = ['/team_user/track/task111']
        c_msg = ChannelMessage(message=data, 
                               cur_user=self.user,
                               received_teams=received_teams,
                               received_pages=received_pages)
        c_msg.broadcast();
        return data
    
class RoutePlanHandler(TeamUserHandler): 
    def init_form_data(self):
        self.page_name = 'Route Plan'
        self.form['action'] = '/team_user/plan/route_plan'
        self.form['dt_source'] = 'RoutePlan'
        self.repeat_field_list = ['driver_set', 'task_set']
        self.form['tb_buttons'] = 'create,edit,delete,export'
        self.form['upload_task_create_warning'] = "Task with the same ID will replace the existing one!"
        self.task_exclude_list =  ['epod', 'sms_log', 'call_log', 'planned_time', 
                                  'planned_datetime','estimated_datetime', 
                                  'finalized_datetime', 'finalized_location', 'fail_count', 
                                  'partial_count', 'task_status', 'remarks']

        self.model_cls = RoutePlan
        self.default_form = 'plan_crud_form.html'
        
    def process_get_form_data(self, form_data):
        form_data = TeamHandler.process_get_form_data(form_data)
        for field in form_data['field_list']:
            #option for role exclude those access level higher than current user
            if field['prop_name'] == 'task_set':
                idx = 0
                while idx < len(field['choices']):
                    task = Task.get_by_id(field['choices'][idx]['_entity_id'])
                    logging.info(task)
                    if (task.task_status != 'Unplanned'): 
                        #remove the option by index
                        field['choices'].pop(idx)
                    else:
                        idx +=1
                        
                        
        form_data['route_task_field_list'] = Task.get_form_fields(
                                    exclude_list=self.task_exclude_list,
                                    cur_user=self.user)
        return form_data            
        
    
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
        self.is_update_user_session = True 
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
    (r'/team_user/set/area$', AreaHandler),
    (r'/team_user/set/address$', AddressHandler),
    (r'/team_user/set/depot$', DepotHandler),
    (r'/team_user/set/depot_template$', DepotTemplateHandler),    
    (r'/team_user/set/vehicle_type$', VehicleTypeHandler),
    (r'/team_user/set/vehicle_type_template$', VehicleTypeTemplateHandler),
    (r'/team_user/set/driver$', DriverHandler),
    (r'/team_user/set/driver_template$', DriverTemplateHandler),
    (r'/team_user/plan/task$', PlanTaskHandler),
    (r'/team_user/plan/route_plan$', RoutePlanHandler),
    (r'/team_user/track/task$', TrackTaskHandler),        
], config=config.WSGI_CONFIG, debug=config.DEBUG)         
    