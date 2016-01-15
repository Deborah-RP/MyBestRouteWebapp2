import logging
import webapp2

import config
from utils.handler_utils import *
from handler.auth import verfication_route
from handler.role_access import TeamHandler, TeamTemplateHandler, UserHandler
from model.account import *
from model.base_doc import *

from model.plan import *

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
        
class AreaHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'Area'
        self.form['action'] = '/team_admin/area'
        self.form['dt_source'] = 'Area'
        self.model_cls = Area
        self.is_audit = True
        self.audit_event_key = 'area_name'   
        
class AddressHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'Address'
        self.form['action'] = '/team_admin/address'
        self.form['dt_source'] = 'Address'
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.form['ajax_search_set_fields'] = 'cust_name,country,city,postal,latlng,unit,building,street,state,area'
        self.is_audit = True
        self.audit_event_key = 'cust_name' 
        self.model_cls = Address

    def process_get_form_data(self, form_data):
        TeamHandler.process_get_form_data(self, form_data)
        return self.set_default_country(form_data)
        
    def process_ajax_search(self):
        result = {}
        if (self.request.get('country') == ""):
            result['ajax_search_message'] = 'Please select a country!'
            return result
        cond_list = self.prepare_cond_list()
        record = self.model_cls.retrieve_existing_address(model_rec=self.request,
                                                          cond_list=cond_list,
                                                          cur_user=self.user)
        
        if DEBUG:
            logging.info("Address from ndb: %s" %record)
        
        if not record:
            record = AddressDocument.get_address_doc_record(self.request)
            logging.info("Address from index: %s" %record)
        '''if not record:
            #record = {}
            #record['ajax_search_message'] = 'Postal code not found in Address Search Index!'
            record = None
        '''
            
        
        result['data'] = record
        if record and len(record) > 1:
            result['ajax_search_message'] = 'Multiple addresses found!'
        elif record == None:
            result['ajax_search_message'] = 'No address found!'
            
        return result
    
    def process_upload_data(self, upload_data):
        for each in upload_data:
            record = AddressDocument.get_address_doc_record(each)
            if record and len(record)>0:
                #Get the first record
                for key in record[0]:
                    if key in each:
                        #Don't change the original value if exist
                        continue
                    else:
                        each[key] = record[0][key]
        return super(AddressHandler, self).process_upload_data(upload_data)
    
class DepotHandler(TeamTemplateHandler):
    def init_form_data(self):
        self.page_name = 'Depot Station'
        self.form['action'] = '/team_admin/depot'
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
        
    def process_get_form_data(self, form_data):
        TeamHandler.process_get_form_data(self, form_data)
        return self.set_default_country(form_data)
        
    def process_ajax_search(self):
        result = {}
        if (self.request.get('country') == ""):
            result['ajax_search_message'] = 'Please select a country!'
            return result
                
        record = AddressDocument.get_address_doc_record(self.request)
        result['data'] = record
        if record and len(record) > 1:
            result['ajax_search_message'] = 'Multiple addresses found!'
        elif record == None:
            result['ajax_search_message'] = 'No address found!'
        return result
    
    def process_upload_data(self, upload_data):
        for each in upload_data:
            record = AddressDocument.get_address_doc_record(each)
            if record and len(record)>0:
                #Get the first record
                for key in record[0]:
                    if key in each:
                        #Don't change the original value if exist
                        continue
                    else:
                        each[key] = record[0][key]
        return super(DepotHandler, self).process_upload_data(upload_data)            
        
class DepotTemplateHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'Depot Station Template'
        self.form['action'] = '/team_admin/depot_template'
        self.form['dt_source'] = 'DepotTemplate'
        self.model_cls = DepotTemplate
        self.is_audit = True
        self.audit_event_key = 'template_name' 

class VehicleTypeHandler(TeamTemplateHandler):
    def init_form_data(self):
        self.page_name = 'Type of Vehicle'
        self.repeat_field_list = ['max_capacities']
        self.form['action'] = '/team_admin/vehicle_type'
        self.form['dt_source'] = 'VehicleType'
        self.model_cls = VehicleType
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'vehicle_type_template'
        self.form['template_search_set_fields'] = 'max_capacities,max_num_order,max_distance,oil_cost_per_km,fixed_cost'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")
        self.default_form = 'crud_ba_form.html'
        self.is_audit = True
        self.audit_event_key = 'type_name'               
        
class VehicleTypeTemplateHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'Vehicle Type Template'
        self.form['action'] = '/team_admin/vehicle_type_template'
        self.form['dt_source'] = 'VehicleTypeTemplate'
        self.repeat_field_list = ['max_capacities']
        self.model_cls = VehicleTypeTemplate
        self.is_audit = True
        self.audit_event_key = 'template_name' 
        
class DriverTemplateHandler(TeamHandler):
    def init_form_data(self):
        self.page_name = 'Driver Template'
        self.form['action'] = '/team_admin/driver_template'
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
    
class DriverHandler(TeamTemplateHandler, DriverTemplateHandler):
    def init_form_data(self):
        self.page_name = 'Driver'
        self.form['action'] = '/team_admin/driver'
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
        
app = webapp2.WSGIApplication([
    (r'/team_admin/users$', TeamAdminUserHandler),                               
    (r'/team_admin/audit_log$', AuditLogHandler),
    (r'/team_admin/area$', AreaHandler),
    (r'/team_admin/address$', AddressHandler),
    (r'/team_admin/depot$', DepotHandler),
    (r'/team_admin/depot_template$', DepotTemplateHandler),    
    (r'/team_admin/vehicle_type$', VehicleTypeHandler),
    (r'/team_admin/vehicle_type_template$', VehicleTypeTemplateHandler),
    (r'/team_admin/driver$', DriverHandler),
    (r'/team_admin/driver_template$', DriverTemplateHandler),
    verfication_route,     
], config=config.WSGI_CONFIG, debug=config.DEBUG)         
    
    