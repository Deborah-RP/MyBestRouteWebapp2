import logging
import json
from google.appengine.ext import ndb
from google.appengine.api import urlfetch

from model.base_model import BaseModel
from model.account import User, BusinessGroup, TeamModel, TemplateModel
from model.base_doc import AddressDocument

import config
from config import DEBUG
'''
    class to define the various zones for the business groups
'''
class Area(TeamModel):
    area_name = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    
    model_display_name = 'area'
    #and hidden check is the group
    unique_and_props = ['area_name']
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.area_name]        
        return order_list
    
    @classmethod
    def prepare_check_key(cls):
        check_existing_key = []
        
        new_check_key = {}
        new_check_key['model_display_name'] = 'address'
        new_check_key['model_cls'] = Address
        new_check_key['other_prop'] = Address.area
        check_existing_key.append(new_check_key)
        
        new_check_key['model_display_name'] = 'depot station'
        new_check_key['model_cls'] = Depot
        new_check_key['other_prop'] = Depot.area
        check_existing_key.append(new_check_key)
                
        new_check_key['model_display_name'] = 'driver'
        new_check_key['model_cls'] = Driver
        new_check_key['other_prop'] = Driver.served_area
        check_existing_key.append(new_check_key)
        
        new_check_key['model_display_name'] = 'task'
        new_check_key['model_cls'] = Task
        new_check_key['other_prop'] = Task.area
        check_existing_key.append(new_check_key)        
       
        return check_existing_key
    
class Address(TeamModel):
    cust_name = ndb.StringProperty(required=True)
    country = ndb.StringProperty(required=True,
                                 choices = config.COUNTRY_LIST, 
                                 verbose_name=','.join(config.COUNTRY_LIST))    
    postal = ndb.StringProperty()
    latlng = ndb.GeoPtProperty()
    unit = ndb.StringProperty()
    building = ndb.StringProperty()
    street = ndb.StringProperty()
    city = ndb.StringProperty()
    state = ndb.StringProperty()
    area = ndb.KeyProperty(kind=Area, verbose_name='area_name')
    formatted_address = ndb.StringProperty()
    
    model_display_name = 'customer address'
    #and hidden check is the group
    unique_and_props = ['cust_name']
    
    @classmethod
    def retrieve_address_dict(cls, 
                                model_rec,
                                cond_list,
                                cur_user,
                                op_type):
        
        cust_name = model_rec.get('cust_name')
        if cust_name != None and cust_name !="":
            cond_list.append(cls.cust_name == cust_name)
        else:
            return None
        
        '''
        for prop_name in cls.unique_and_props:
            prop_val = model_rec.get(prop_name)
            prop_val = cls.init_prop_val(prop_val)
            if prop_val == None:
                continue
            #get the model property based on its name(string) 
            model_prop = cls._properties[prop_name]
            #add to cond_list
            cond_list.append(model_prop==prop_val)
            
        if DEBUG:
            logging.info('cond_list:%s' %(cond_list))
        '''
           
        addr_dict = cls.query_data_to_dict(cond_list=cond_list, 
                                      cur_user=cur_user)
        
        
        if (len(addr_dict) > 0 and op_type != 'upload'):
            if addr_dict[0]['area'] != None and addr_dict[0]['area'] != "":
                addr_dict[0]['area'] = cls.get_entity_id_by_value(prop_name='area', 
                                                       prop_val=addr_dict[0]['area'], 
                                                       model_rec=model_rec, 
                                                       cur_user=cur_user)
        return addr_dict
                 
    
    '''
    @classmethod
    def create_from_sgpostal(cls, postal, business_group, user_created, business_team):
        query_result = cls.query(ndb.AND(cls.postal==postal,
                                         cls.business_group==business_group,
                                         cls.business_team==business_team))
        address_entity = query_result.get()        
        
        if not address_entity:
            address_record = AddressDocument.get_record_dict(postal)
            if address_record:
                address_entity = cls(postal=postal)
                address_entity.latlng = ndb.GeoPt(address_record['latlng'])
                address_entity.street = address_record['street']
                address_entity.block = address_record['block']
                address_entity.building = address_record['building']
                address_entity.formatted_address = address_record['formatted_address']
                address_entity.business_group = business_group
                address_entity.user_created = user_created
                address_entity.business_team = business_team
                address_entity.put()
            else:
                address_entity = None
        return address_entity
    '''
    @staticmethod
    def get_format_address(model_rec, record):
        model_rec['latlng'] = record['latlng']
        if "#" not in record['formatted_address']:
            if 'unit' in model_rec and model_rec['unit'] != "":
                if not model_rec['unit'].startswith("#"):
                    model_rec['unit'] = "#" + model_rec['unit']
                if record['formatted_address'] != None:
                    tmp_address = record['formatted_address'].split(",")
                    tmp_address[len(tmp_address)-2] += " " + model_rec['unit']
                    model_rec['formatted_address'] = ','.join(tmp_address)
                else:
                    model_rec['formatted_address'] = record['formatted_address']
        else:
            model_rec['formatted_address'] = record['formatted_address']
        return model_rec                    

    
    @classmethod
    def set_geolocation(cls, 
                        model_rec,
                        cond_list,
                        cur_user,
                        op_type):
        
        addr_attr_list = ['unit', 'postal', 'building', 'street', 'city', 'state', 'area']
        record = cls.search_address_record(model_rec, 
                                           cond_list, 
                                           cur_user,
                                           op_type)
        
        if record:
            if len(record) > 0:
                record = record[0]
            model_rec['latlng'] = record['latlng']
            
            model_rec = cls.get_format_address(model_rec, record)
            logging.info(model_rec) 
            for prop_name in addr_attr_list:
                if prop_name in model_rec and model_rec[prop_name] != "":
                    continue
                elif prop_name in record:
                    model_rec[prop_name] = record[prop_name]
        return model_rec    
    
    @classmethod
    def search_address_record(cls,
                       model_rec,
                       cond_list,
                       cur_user,
                       op_type=None):
        record = Address.retrieve_address_dict(model_rec, 
                                               cond_list, 
                                               cur_user,
                                               op_type=op_type)
        logging.info(record)
        if record == None or len(record) == 0:
            record = AddressDocument.get_address_doc_record(model_rec)
            
        #if record and len(record) > 0:
        #    record = record[0]
            
        return record        
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.postal]        
        return order_list
    
class DepotTemplate(TemplateModel):
    loading_duration = ndb.IntegerProperty(default=0)
    unloading_duration = ndb.IntegerProperty(default=0)        
    
    model_display_name = 'depot station template'
    #and hidden check is the group
    unique_and_props = ['template_name']
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.template_name]
        return order_list        

class Depot(TeamModel):
    depot_name = ndb.StringProperty(required=True)
    country = ndb.StringProperty(required=True,
                                 choices = config.COUNTRY_LIST, 
                                 verbose_name=','.join(config.COUNTRY_LIST))    
    postal = ndb.StringProperty()
    latlng = ndb.GeoPtProperty()
    unit = ndb.StringProperty()
    building = ndb.StringProperty()
    street = ndb.StringProperty()
    city = ndb.StringProperty()
    state = ndb.StringProperty()
    area = ndb.KeyProperty(kind=Area, verbose_name='area_name')
    formatted_address = ndb.StringProperty()

    loading_duration = ndb.IntegerProperty(default=0)
    unloading_duration = ndb.IntegerProperty(default=0)
    
    depot_template = ndb.KeyProperty(kind=DepotTemplate, verbose_name='template_name')
    model_display_name = 'depot station'
    #and hidden check is the group
    unique_and_props = ['depot_name']
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.depot_name]        
        return order_list
    
    @classmethod
    def prepare_check_key(cls):
        check_existing_key = []
        
        new_check_key = {}
        
        new_check_key['model_display_name'] = 'driver'
        new_check_key['model_cls'] = Driver
        new_check_key['other_prop'] = Driver.start_address
        check_existing_key.append(new_check_key)
        
        new_check_key['model_display_name'] = 'driver'
        new_check_key['model_cls'] = Driver
        new_check_key['other_prop'] = Driver.end_address
        check_existing_key.append(new_check_key)
        return check_existing_key    
    
    '''@classmethod
    def prepare_create_data(cls, 
                            model_rec, 
                            unique_id=None, 
                            is_unique=True, 
                            op_type=None,
                            cur_user=None):
        
        
        #postal is the text value, need to convert to id
        if op_type != 'upload':
            postal = model_rec.get('postal')
            result = cls.convert_keyprop_by_value('postal', 
                                                  postal, 
                                                  mode_rec=model_rec,
                                                  cur_user=cur_user)
            if result['status'] == True:
                address_id = result['key'].id()
                model_rec['postal'] = address_id

        return model_rec
    '''
    
    '''
    @classmethod
    def prepare_update_data(cls, model_rec, 
                            unique_id=None, 
                            is_unique=True, 
                            cur_user=None):
        
        #postal is the text value, need to convert to id
        postal = model_rec.get('postal')
        result = cls.convert_keyprop_by_value('postal', 
                                                postal, 
                                                model_rec=model_rec,
                                                cur_user=cur_user)
        if result['status'] == True:
            address_id = result['key'].id()
            model_rec['postal'] = address_id

        return model_rec
    '''

class Capacity(BaseModel):
    unit = ndb.StringProperty(required=True)
    value = ndb.FloatProperty(required=True)
    
    '''
        Convert the string input into a entity
        The string input format should be unit:value
    '''
    @classmethod
    def process_structured_prop(cls, prop_val):
        prop_val_list = prop_val.split(":")
        capacity = Capacity()
        capacity.unit = prop_val_list[0]
        capacity.value = float(prop_val_list[1])
        return capacity
    
    @classmethod
    def _struct_prop_to_str(cls, prop_val):
        prop_str = ""
        idx = 0
        while idx < len(prop_val):
            each = prop_val[idx]
            prop_str += "%s:%s" %(each.unit, each.value)
            if idx < (len(prop_val)-1):
                prop_str +=","
            idx += 1
        return prop_str
    
class VehicleTypeTemplate(TemplateModel):
    max_capacities = ndb.StructuredProperty(Capacity, repeated=True)
    max_num_order = ndb.IntegerProperty()
    max_distance = ndb.FloatProperty()
    oil_cost_per_km = ndb.FloatProperty()
    fixed_cost = ndb.FloatProperty()
    
    model_display_name = 'vehicle type template'
    #and hidden check is the group
    unique_and_props = ['template_name']
    

class VehicleType(TeamModel):
    type_name = ndb.StringProperty(required=True)
    vehicle_type_template = ndb.KeyProperty(kind=VehicleTypeTemplate, verbose_name='template_name')
    max_capacities = ndb.StructuredProperty(Capacity, repeated=True)
    max_num_order = ndb.IntegerProperty()
    max_distance = ndb.FloatProperty()
    oil_cost_per_km = ndb.FloatProperty()
    fixed_cost = ndb.FloatProperty()
    model_display_name = 'vehicle type'
    unique_and_props = ['type_name']
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.type_name]        
        return order_list
    
    @classmethod
    def prepare_check_key(cls):
        check_existing_key = []
        new_check_key = {}
        new_check_key['model_display_name'] = 'driver'
        new_check_key['model_cls'] = Driver
        new_check_key['other_prop'] = Driver.vehicle_type
        check_existing_key.append(new_check_key)
                
        return check_existing_key    
    
class DriverTemplate(TemplateModel):
    vehicle_info = ndb.StringProperty()
    served_area = ndb.KeyProperty(kind=Area, verbose_name='area_name')
    start_address = ndb.KeyProperty(kind=Depot, verbose_name='depot_name')
    end_address = ndb.KeyProperty(kind=Depot, verbose_name='depot_name')
    speed_factor = ndb.FloatProperty()
    work_start_time = ndb.TimeProperty()
    work_end_time = ndb.TimeProperty()
    max_work_hour = ndb.FloatProperty()
    break_start_time = ndb.TimeProperty()
    break_end_time = ndb.TimeProperty()
    break_duration = ndb.IntegerProperty()
    skills = ndb.StringProperty(repeated=True)
    cost_per_hour = ndb.FloatProperty()
    overwork_rate_per_hour = ndb.FloatProperty()

    
    model_display_name = 'driver template'
    unique_and_props = ['template_name']
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.template_name]
        return order_list
    
class Driver(TeamModel):
    driver_name = ndb.StringProperty(required=True)
    vehicle_type = ndb.KeyProperty(required=True, kind=VehicleType, verbose_name='type_name')
    driver_pin = ndb.StringProperty()
    gps_interval = ndb.IntegerProperty(default=0)
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    driver_template = ndb.KeyProperty(kind=DriverTemplate, verbose_name='template_name')
    vehicle_info = ndb.StringProperty()
    served_area = ndb.KeyProperty(kind=Area, verbose_name='area_name')
    start_address = ndb.KeyProperty(kind=Depot, verbose_name='depot_name')
    end_address = ndb.KeyProperty(kind=Depot, verbose_name='depot_name')
    speed_factor = ndb.FloatProperty()
    work_start_time = ndb.TimeProperty()
    work_end_time = ndb.TimeProperty()
    max_work_hour = ndb.FloatProperty()
    break_start_time = ndb.TimeProperty()
    break_end_time = ndb.TimeProperty()
    break_duration = ndb.IntegerProperty()
    skills = ndb.StringProperty(repeated=True)
    cost_per_hour = ndb.FloatProperty()
    overwork_rate_per_hour = ndb.FloatProperty()    
    
    model_display_name = 'driver'
    #and hidden check is the group
    unique_and_props = ['driver_name']    
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.driver_name]
        return order_list
    
    @classmethod
    def prepare_check_key(cls):
        check_existing_key = []
        new_check_key = {}
        new_check_key['model_display_name'] = 'task'
        new_check_key['model_cls'] = Task
        new_check_key['other_prop'] = Task.driver
        check_existing_key.append(new_check_key)
                
        return check_existing_key        
    
class ClientAccount(TeamModel):
    acct_name = ndb.StringProperty(required=True)
    notify_added = ndb.StringProperty(repeated=True)
    notify_deleteded = ndb.StringProperty(repeated=True)
    notify_finalized = ndb.StringProperty(repeated=True)
    notify_failed = ndb.StringProperty(repeated=True)
    notify_partial = ndb.StringProperty(repeated=True)
    notify_lapsed = ndb.StringProperty(repeated=True)
       
    '''
    emails = ndb.StringProperty(repeated=True)
    notify_added = ndb.BooleanProperty(default=False)
    notify_deleteded = ndb.BooleanProperty(default=False)
    notify_finalized = ndb.BooleanProperty(default=False)
    notify_failed = ndb.BooleanProperty(default=False)
    notify_partial = ndb.BooleanProperty(default=False)
    notify_lapsed = ndb.BooleanProperty(default=False)
    '''
    
    model_display_name = 'client account'
    unique_and_props = ['acct_name']
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.acct_name]
        return order_list
    
    @classmethod
    def prepare_check_key(cls):
        check_existing_key = []
        new_check_key = {}
        new_check_key['model_display_name'] = 'task'
        new_check_key['model_cls'] = Task
        new_check_key['other_prop'] = Task.client_account
        check_existing_key.append(new_check_key)
                
        return check_existing_key           

class Task(TeamModel):
    task_id = ndb.StringProperty(required=True)
    task_type = ndb.StringProperty(required=True, default='Delivery', choices= config.ORDER_TYPE)
    
    cust_name = ndb.StringProperty()
    country = ndb.StringProperty(required=True,
                                 choices = config.COUNTRY_LIST, 
                                 verbose_name=','.join(config.COUNTRY_LIST))      
    postal = ndb.StringProperty()
    latlng = ndb.GeoPtProperty()
    unit = ndb.StringProperty()
    building = ndb.StringProperty()
    street = ndb.StringProperty()
    city = ndb.StringProperty()
    state = ndb.StringProperty()
    area = ndb.KeyProperty(kind=Area, verbose_name='area_name')
    formatted_address = ndb.StringProperty()
    planned_date = ndb.DateProperty(required=True)
    planned_time = ndb.TimeProperty()
    
    cust_emails = ndb.StringProperty(repeated=True)
    cust_phones = ndb.StringProperty(repeated=True)
    client_account = ndb.KeyProperty(kind=ClientAccount, verbose_name='acct_name')
    order_id = ndb.StringProperty()
    driver = ndb.KeyProperty(kind=Driver, verbose_name='driver_name')
    depot_station = ndb.KeyProperty(kind=Depot, verbose_name='depot_name')
    service_duration = ndb.IntegerProperty()
    time_window_from = ndb.TimeProperty()
    time_window_to = ndb.TimeProperty()
    priority = ndb.StringProperty(default='Normal', choices=config.PRIORITY_LIST, verbose_name=','.join(config.PRIORITY_LIST))
    load_unit = ndb.StringProperty()
    load_quantity = ndb.FloatProperty()
    required_skills = ndb.StringProperty(repeated=True)
    job_count = ndb.FloatProperty(default=1.0)
    task_status = ndb.StringProperty(required=True, choices=config.TASK_STATUS)
    epod = ndb.BlobKeyProperty(repeated=True)
    sms_log = ndb.StringProperty(repeated=True, indexed=False)
    call_log = ndb.StringProperty(repeated=True, indexed=False)
    instruction = ndb.TextProperty()
    remarks = ndb.StringProperty()
    planned_datetime = ndb.DateTimeProperty()
    estimated_datetime = ndb.DateTimeProperty()
    finalized_datetime = ndb.DateTimeProperty()
    finalized_location = ndb.GeoPtProperty()
    fail_count = ndb.IntegerProperty(default=0)
    partial_count = ndb.IntegerProperty(default=0)
    
    model_display_name = 'Task'
    #and hidden check is the group
    unique_and_props = ['task_id']
    
    is_replaced = True
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [-cls.tm_updated]
        return order_list
    
    #Allow the task with the same id to replace the existing one.
    @classmethod
    def create_model_entity(cls, model_rec, 
        unique_id=None, 
        is_unique=True, 
        op_type=None, 
        cur_user=None):
        return super(Task, cls).create_model_entity(model_rec, 
                                                    unique_id=unique_id, 
                                                    is_unique=False, 
                                                    op_type=op_type, 
                                                    cur_user=cur_user)
    
class RoutePlan(TeamModel):
    route_plan_name = ndb.StringProperty(required=True)
    driver_set = ndb.KeyProperty(repeated=True, kind=Driver, verbose_name='driver_name')
    task_set = ndb.KeyProperty(repeated=True, kind=Task, verbose_name='task_id')
    plan_status = ndb.StringProperty(default='Open', choices=config.ROUTE_PLAN_STATUS)
    route_plan_updated = ndb.DateTimeProperty(auto_now=True)
    submit_and_optimized = ndb.StringProperty(default="Yes", choices=["Yes", "No"])
    optimized_algo = ndb.StringProperty(choices=['Ortec'])
    
    model_display_name = 'customer order';
    #and hidden check is the group
    unique_and_props = ['route_plan_name']    
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [-cls.route_plan_updated]
        return order_list    
     
