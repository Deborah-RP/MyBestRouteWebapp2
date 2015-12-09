import logging
import webapp2

from model.account import UserRole, BusinessGroup
from utils.handler_utils import *
from handler.base import BaseHandler, CRUDHandler

from model.account import User
from model.plan import *
from model.base_doc import *
import config

class GroupUserHandler(CRUDHandler):
    @webapp2.cached_property
    def min_access_level(self):
        user_role = UserRole.query(UserRole.role_name == config.GROUP_USER).get()
        return user_role.access_level
    
    @webapp2.cached_property
    def business_id(self):
        return self.user.business_group.get().key.id()
    
    def post(self):
        self.request.POST['business_group'] = str(self.business_id)
        self.request.POST['user_created'] = str(self.user.key.id())
        super(GroupUserHandler, self).post()
        
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each['business_group'] = self.user.business_group
            each['user_created'] = self.user.key
        return upload_data
        
    def async_query_all_json(self):
        super(GroupUserHandler, self).async_query_all_json(user_business_group=self.user.business_group)
    
class GroupTemplateHandler(GroupUserHandler):
    def process_template_search(self):
        #Get template key based on id
        template_field_id = self.form['template_search_get_fields']
        template_id = self.request.get(template_field_id)

        if template_id:
            result = self.model_cls.convert_keyprop_by_id(template_field_id, template_id)
            if result['status'] == False:
                result['ajax_search_message'] = result['message']
                return result
            else:
                template_key = result['key']
                return template_key.get().to_dict()
        return None
    
    def process_upload_data(self, upload_data):
        template_field_id = self.form['template_search_get_fields']
        for each in upload_data:
            each = self.set_template_value(template_field_id, each)
        return GroupUserHandler.process_upload_data(self, upload_data)                 

class AreaHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Area'
        self.form['action'] = '/user/area'
        self.form['dt_source'] = 'Area'
        self.model_cls = Area
        
class AddressHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Address'
        self.form['action'] = '/user/address'
        self.form['dt_source'] = 'Address'
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'postal,block,street,building'
        self.form['ajax_search_set_fields'] = 'postal,latlng,block,street,building'
        self.model_cls = Address
    
    def process_ajax_search(self):
        check_result = self.model_cls.check_unique_value(self.request, self.user.business_group)
        if check_result['status'] != True:
            record = {}
            record['ajax_search_message'] = 'Postal address already added in the group, please edit the record instead!'
            return record
        
        record = SGPostal.get_sgpostal_record(self.request)
        if not record:
            record = {}
            record['ajax_search_message'] = 'Postal code not found in Singapore Postal Index!'
        return record
    
    def process_upload_data(self, upload_data):
        for each in upload_data:
            record = SGPostal.get_sgpostal_record(each)
            if record:
                for key in record:
                    if key in each:
                        #Don't change the original value if exist
                        continue
                    else:
                        each[key] = record[key]
        return super(AddressHandler, self).process_upload_data(upload_data)
    
class DepotHandler(GroupTemplateHandler):
    def init_form_data(self):
        self.page_name = 'Depot Station'
        self.form['action'] = '/user/depot'
        self.form['dt_source'] = 'Depot'
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'postal'
        self.form['ajax_search_set_fields'] = ''
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'depot_template'
        self.form['template_search_set_fields'] = 'loading_duration,unloading_duration'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")      
        self.model_cls = Depot
        
    def process_ajax_search(self):
        check_result = Address.check_unique_value(self.request, self.user.business_group)
        if check_result['status'] == True:
            record = {}
            record['ajax_search_message'] = "Please add the postal address via 'Manage Address' first!"
            return record
        
class DepotTemplateHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Depot Station Template'
        self.form['action'] = '/user/depot_template'
        self.form['dt_source'] = 'DepotTemplate'
        self.model_cls = DepotTemplate                

class VehicleTypeHandler(GroupTemplateHandler):
    def init_form_data(self):
        self.page_name = 'Type of Vehicle'
        self.repeat_field_list = ['max_capacities']
        self.form['action'] = '/user/vehicle_type'
        self.form['dt_source'] = 'VehicleType'
        self.model_cls = VehicleType
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'vehicle_type_template'
        self.form['template_search_set_fields'] = 'max_capacities,max_number_of_order,max_distance,oil_cost_per_km,fixed_cost'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")      
        
class VehicleTypeTemplateHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Vehicle Type Template'
        self.form['action'] = '/user/vehicle_type_template'
        self.form['dt_source'] = 'VehicleTypeTemplate'
        self.repeat_field_list = ['max_capacities']
        self.model_cls = VehicleTypeTemplate
        
class DriverTemplateHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Driver Template'
        self.form['action'] = '/user/driver_template'
        self.form['dt_source'] = 'DriverTemplate'
        self.repeat_field_list = ['skills']
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'start_address,end_address'
        self.form['ajax_search_set_fields'] = ''
        self.model_cls = DriverTemplate
    
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
    
    def process_address(self, model_rec):
        address_list = {}
        address_list['start_address'] = model_rec.get('start_address').strip()
        address_list['end_address'] = model_rec.get('end_address').strip()
            
        for address_id in address_list:
            postal = address_list[address_id]
            business_group = self.user.business_group
            user_created = self.user.key                
            address_entity = Address.create_from_sgpostal(postal, business_group, user_created)
            model_rec[address_id] = address_entity.key
        return model_rec
    
    def process_create_data(self, model_rec):
        return self.process_address(model_rec)  
    
    def process_edit_data(self, model_rec):
        return self.process_address(model_rec)
    
class DriverHandler(GroupTemplateHandler, DriverTemplateHandler):
    def init_form_data(self):
        self.page_name = 'Driver'
        self.form['action'] = '/user/driver'
        self.form['dt_source'] = 'Driver'
        self.repeat_field_list = ['skills']
        self.model_cls = Driver
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'start_address,end_address'
        self.form['ajax_search_set_fields'] = ''        
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'driver_template'
        self.form['template_search_set_fields'] = 'vehicle_info,served_area,start_address,end_address,speed_factor,work_start_time,work_end_time,max_work_hour,break_start_time,break_end_time,break_duration,skills,cost_per_hour,overwork_rate_per_hour'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")
        
class CustOrderHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Customer Order'
        self.form['action'] = '/user/cust_order'
        self.form['dt_source'] = 'CustOrder'
        self.repeat_field_list = ['required_skills']
        self.model_cls = CustOrder
        self.form['ajax_search_url'] = self.form['action']
        self.form['ajax_search_get_fields'] = 'postal'
        self.form['ajax_search_set_fields'] = ''        
        self.form['template_search_url'] = self.form['action']
        self.form['template_search_get_fields'] = 'driver_template'
        self.form['template_search_set_fields'] = 'vehicle_info,served_area,start_address,end_address,speed_factor,work_start_time,work_end_time,max_work_hour,break_start_time,break_end_time,break_duration,skills,cost_per_hour,overwork_rate_per_hour'
        self.template_upload_set_list = self.form['template_search_set_fields'].split(",")
        
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
        address_entity = Address.create_from_sgpostal(postal, business_group, user_created)
        model_rec['postal'] = address_entity.key
        return model_rec
    
    def process_create_data(self, model_rec):
        return self.process_address(model_rec)  
    
    def process_edit_data(self, model_rec):
        return self.process_address(model_rec)
    
class RoutePlanHandler(GroupUserHandler): 
    def init_form_data(self):
        self.page_name = 'Route Plan'
        self.form['action'] = '/user/route_plan'
        self.form['dt_source'] = 'RoutePlan'
        self.model_cls = RoutePlan
        
    def get(self):
        self.form['field_list'] = self.model_cls.get_form_fields(
                                    self.form_include_list, 
                                    self.form_exclude_list,
                                    self.user.business_group)
        self.render("plan_crud_form.html", form=self.form)        
    
class UserProfileHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'User Profile'
        self.form['action'] = '/user/user_profile'
        self.form['dt_source'] = 'User'
        self.model_cls = User 
        self.edit_include_list = ['_entity_id', 'email', 'user_name', 'created', 'last_login_time']
        
    def get(self):
        model_entity = self.user
        self.get_edit(model_entity)
        
    def async_edit(self):
        self.request.POST['user_access_level'] = self.user.access_level
        super(UserProfileHandler, self).async_edit()         
        
class ChangePasswordHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'Password'
        self.form['action'] = '/user/change_password'
        
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
        
class ChangePricePlanHandler(GroupUserHandler):
    def init_form_data(self):
        self.page_name = 'price plan'
        self.form['action'] = '/user/change_priceplan'
        self.form['dt_source'] = PricePlan
        self.model_cls = get_kind_by_name(self.form['dt_source'])
        self.table_exclude_list = ['_entity_id', 'plan_created', 'plan_updated']
        self.edit_include_list = ['_entity_id', 'price_plan']   
        self.number_id = True       
        
    def get(self):    
        model_entity = self.user
        self.form['field_list'] = User.get_form_fields(self.edit_include_list)
        tmp_obj = model_entity.entity_to_dict()
        for field in self.form['field_list']:
            prop_name = field['prop_name']
            field['value'] = tmp_obj[prop_name]
        self.render("table_update_form.html", form=self.form)

        #Only group admin and personal user can perform this operation.
        
        #For personal user in default group, create a new business group
        
        #Otherwise, update the group information
    def async_edit(self):
        '''post_dict = {}
        for key in self.request.POST:
            if self.edit_include_list and key not in self.edit_include_list:
                continue
            
            if self.edit_exclude_list and key in self.edit_exclude_list:
                continue
            
            post_dict[key] = self.request.POST[key]
        status, msg = User.update_model_entity(post_dict, self.number_id)
        '''
        self.async_render_msg(True, "Pending for implementation.")       

app = webapp2.WSGIApplication([
    (r'/user/user_profile$', UserProfileHandler),
    (r'/user/change_password$', ChangePasswordHandler),
    (r'/user/change_priceplan$', ChangePricePlanHandler),
    (r'/user/area$', AreaHandler),
    (r'/user/address$', AddressHandler),
    (r'/user/depot$', DepotHandler),
    (r'/user/depot_template$', DepotTemplateHandler),    
    (r'/user/vehicle_type$', VehicleTypeHandler),
    (r'/user/vehicle_type_template$', VehicleTypeTemplateHandler),
    (r'/user/driver$', DriverHandler),
    (r'/user/driver_template$', DriverTemplateHandler),
    (r'/user/cust_order$', CustOrderHandler),
    (r'/user/route_plan$', RoutePlanHandler),    
], config=config.WSGI_CONFIG, debug=config.DEBUG)         
    
    