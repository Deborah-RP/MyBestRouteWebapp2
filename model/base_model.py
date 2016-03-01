import logging
import config
import datetime
from datetime import tzinfo, timedelta

from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
from utils.exception_utils import ExpHandleAll
from config import DEBUG, GROUP_UNIQUE

#class of timezone, inherit abstract class tzinfo
class UserTimeZone(tzinfo):
    def __init__(self, offset=8, name=None):
        self.offset = timedelta(hours=offset)
        self.name = name or self.__class__.__name__

    def utcoffset(self, dt):
        return self.offset

    def tzname(self, dt):
        return self.name

    def dst(self, dt):
        return timedelta(0)

#Return the ndb kind based on the given name (string)
def _get_kind_by_name(kind_name):
    kind_map = ndb.Model._kind_map
    model_cls = kind_map[kind_name]
    return model_cls

'''
    Return kind name and property name or KeyProperty
    The property name is stored in the verbose_name attribute
'''
def _get_keyprop_attr(key_prop):
    model_cls = _get_kind_by_name(key_prop._kind)
    prop_name = key_prop._verbose_name
    return model_cls, prop_name

class BaseModel(ndb.Model):
    
    '''
        Property to indicate if the record has been deleted
        True means record still available, False means record has been deleted
        This is to avoid the key error in datastore
        ** Not used at the moment
    '''
    is_active = ndb.BooleanProperty(default=True)
    tm_created = ndb.DateTimeProperty(auto_now_add=True)
    tm_updated = ndb.DateTimeProperty(auto_now=True)   
    
    unique_or_props = []
    unique_and_props = []
    is_number_id = True
    model_display_name = ""
    unique_level = config.SYSTEM_UNIQUE.unique_level
    '''
    is_group_search = False
    is_team_search = False
    '''
    is_replaced = False
    
    '''
        Get condition list for query
        based on the is_group_search value 
        to decide if the search should be within 
        the user group
    '''
    
    '''
    @classmethod
    def get_cond_list(cls, 
                      cond_list = None, 
                      user_business_group = None, 
                      user_business_team = None):
        if cls.is_group_search:
            if user_business_group:
                #For empty list
                if cond_list == None:
                    cond_list = [cls.business_group == user_business_group]
                else:
                    cond_list.append(cls.business_group == user_business_group)
                    
                if cls.is_team_search:
                    if user_business_team:
                        cond_list.append(cls.business_team == user_business_team)
                    else:
                        logging.info("get_cond_list: Business team is empty.")
            else:
                logging.info("get_cond_list: Business group is empty.")
        return cond_list
    '''
    


    '''method to query model data with specified condition and order'''
    @classmethod
    def _model_query(cls,
                    cur_user=None, 
                    cond_list=None, 
                    order_list=None):
        #Check the business_group and business_team
        '''
        if ((cls.is_group_search==True and user_business_group==None) or
            (cls.is_team_search==True and user_business_team==None)):
            return None
        '''
        
        #Decide if the search need to include the group condition
        '''
        cond_list = cls.get_cond_list(cond_list=cond_list, 
                                      user_business_group=user_business_group,
                                      user_business_team=user_business_team)
        
        '''

        if cond_list == None:
            query_result = cls.query()
        else:
            query_result = cls.query(*cond_list)
        
        if order_list:
            result_list = query_result.order(*order_list).fetch()
        else:
            result_list = query_result.fetch()
  
        return result_list
    
    '''Convert the structure property into a string'''
    @classmethod
    def _struct_prop_to_str(cls, prop_val):
        return prop_val
    
    '''Get the display value of the key property
        Usually use for frontend UI
    '''
    def _get_keyprop_display_value(self, key_val, key_prop_name):
            key_entity = key_val.get()
            #get the display value of the KeyProperty
            if key_entity:
                return getattr(key_entity, key_prop_name)
            #if the key doesn't exist anymore
            else:
                return None            
    '''
    method to overwrite the to_dict() function
    for special handling of properties such as 
    KeyProperty and DateTimeProperty
    '''
    def to_dict(self,
                cur_user, 
                is_with_entity_id=True): 
        key_dict = {}
        date_list = []
        time_list = []
        dt_ajust_list = []
        geo_list = []
        struct_list = []
        for prop_name in self._properties:
            prop_type = self._properties[prop_name].__class__.__name__
            #Get the property that represent the KeyProperty display value
            if prop_type == 'KeyProperty':
                key_dict[prop_name] = self._properties[prop_name]._verbose_name
            elif prop_type == 'DateProperty':
                date_list.append(prop_name)
            elif prop_type == 'TimeProperty':
                time_list.append(prop_name)                
            elif prop_type == 'DateTimeProperty':
                dt_ajust_list.append(prop_name)
            elif prop_type == 'GeoPtProperty':
                geo_list.append(prop_name)
            elif prop_type == 'StructuredProperty':
                struct_list.append(prop_name)
        
        #call the to_dict in the super class
        tmp_obj = super(BaseModel, self).to_dict()
        
        
        #get the other entity based on key
        for prop_name in key_dict:
            #Get the key value of the other entity based on the current entity
            key_val = getattr(self, prop_name)
            if key_val != None:
                key_prop_name = key_dict[prop_name]
                if isinstance(key_val, list):
                    key_val_list = []
                    for each_key_val in key_val:
                        each_key_val = self._get_keyprop_display_value(each_key_val, key_prop_name)
                        key_val_list.append(each_key_val)
                    tmp_obj[prop_name] = key_val_list
                else: 
                    tmp_obj[prop_name] = self._get_keyprop_display_value(key_val, key_prop_name)
        
        #for the StructuredProperty
        for prop_name in struct_list:
            if tmp_obj[prop_name] != None:
                struct_obj = getattr(self, prop_name)
                prop_model_cls = self._properties[prop_name]._modelclass
                #print prop_model_cls
                tmp_obj[prop_name] = prop_model_cls._struct_prop_to_str(struct_obj)
        
        #for date and time property
        for prop_name in date_list:
            if tmp_obj[prop_name] != None:
                date_obj = getattr(self, prop_name)
                tmp_obj[prop_name] = date_obj.strftime("%d/%m/%Y")
                 

        for prop_name in time_list:
            if tmp_obj[prop_name] != None:
                time_obj = getattr(self, prop_name)
                tmp_obj[prop_name] = time_obj.strftime('%H:%M')
                
        #for datetime property
        for prop_name in dt_ajust_list:
            if tmp_obj[prop_name] != None:
                dt_obj = getattr(self, prop_name)
                
                #define UTC timezone
                UTC = UserTimeZone(offset=0)
                
                #if user team/group is not available, assume the default timezone (+8)
                user_tz = cur_user.user_timezone
                dt_obj = dt_obj.replace(tzinfo=UTC).astimezone(user_tz)
                #tmp_obj[prop_name] = dt_obj.isoformat()
                tmp_obj[prop_name] = dt_obj.strftime('%d/%m/%Y %H:%M')         
        
        #for geopoint property
        for prop_name in geo_list:
            if tmp_obj[prop_name] != None:
                geo_obj = getattr(self, prop_name)
                tmp_obj[prop_name] = (geo_obj.lat, geo_obj.lon)
        
        if is_with_entity_id == True:
            tmp_obj['_entity_id'] = self.key.id()
    
        return tmp_obj    
    
    '''method to prepare the query order list'''
    @classmethod
    def prepare_query_order(cls, order_list):
        return order_list
    
    '''method to prepare the query condition list'''
    @classmethod
    def prepare_query_cond(cls, cond_list):
        return cond_list
    
    '''method to query data and convert to dictionary'''
    @classmethod
    def query_data_to_dict(cls,
                           cur_user, 
                           cond_list=None, 
                           order_list=None, 
                           is_with_entity_id=True):
        
        order_list = cls.prepare_query_order(order_list)
        cond_list = cls.prepare_query_cond(cond_list)
        
        result_list = cls._model_query(cur_user=cur_user, 
                                       cond_list=cond_list, 
                                       order_list=order_list)
        

        tmp_list = []
        if result_list != None:
            for each in result_list:
                tmp_obj = each.to_dict(is_with_entity_id=is_with_entity_id, 
                                       cur_user=cur_user)
                tmp_list.append(tmp_obj)
        return tmp_list
    
    @classmethod
    def _get_unique_and_query(cls, 
                             model_rec, 
                             cur_user,
                             op_type=None):
        and_query = None
   
        '''tmp_result = cls.get_data_from_rec(model_rec=model_rec, 
                                           cur_user=cur_user,
                                           op_type=op_type)
        print tmp_result

        if tmp_result['status'] != True:
            logging.error('get_unique_and_query: %s' %tmp_result['message'])
        else:
            tmp_result = tmp_result['data']
        '''
        
        #check the unique_and_props first
        if len(cls.unique_and_props) > 0:
            #limit the check within the group
            and_query = cls.query()
            if cls.unique_level >= config.GROUP_UNIQUE.unique_level:
                if 'business_group' not in cls.unique_and_props:
                    result=cls._convert_key_data_to_prop('business_group', 
                                                        model_rec=model_rec, 
                                                        cur_user=cur_user, 
                                                        op_type=op_type)
                    if result['status'] == False:
                        logging.error(result['message'])
                    else:
                        user_business_group = result['key']
                        and_query=and_query.filter(cls.business_group==user_business_group)
                          
            if cls.unique_level >= config.TEAM_UNIQUE.unique_level:
                if 'business_team' not in cls.unique_and_props:
                    result=cls._convert_key_data_to_prop('business_team', 
                                                        model_rec=model_rec, 
                                                        cur_user=cur_user, 
                                                        op_type=op_type)
                    if result['status'] == False:
                        logging.error(result['message'])
                    else:
                        user_business_team = result['key']
                        and_query=and_query.filter(cls.business_team==user_business_team)
                
            for prop_name in cls.unique_and_props:
                    prop_val = model_rec.get(prop_name)
                    #prop_val = cls.init_prop_val(prop_val)
                    #get the model property based on its name(string) 
                    model_prop = cls._properties[prop_name]
                    #filter result with the condition
                    and_query = and_query.filter(model_prop==prop_val)
                    #if DEBUG:
                        #logging.info('prop:%s query:%s' %(prop_name, and_query.fetch()))
         
        return and_query        
    
    '''
        check if the model record is unique based on
        property define in unique_or_props and unique_and_props
        return value: result (dictionary)
                  - status: bool True is unqiue, False is not unique
                  - message: detail information about the check
                  - entity: the entity from the query result
    '''
   
    @classmethod
    def check_unique_value(cls, 
                           model_rec, 
                           cur_user, 
                           op_type=None): 
        result = {}
        result['status'] = True
        result['message'] = ""
        result['entity'] = None
        
        and_query = cls._get_unique_and_query(model_rec=model_rec, 
                                             cur_user=cur_user,
                                             op_type=op_type)
                                             
        if and_query:
            query_result = and_query.fetch()
        else:
            query_result = None
            
        if query_result:
            msg = '+'.join(cls.unique_and_props)
            msg = msg + " already exists"
            result['status'] = False
            result['message'] = msg
            result['entity'] = query_result[0]
            return result
        
        #check entity with or condition
        if (len(cls.unique_or_props)):
            for prop_name in cls.unique_or_props:
                prop_val = model_rec.get(prop_name)
                prop_val = cls.init_prop_val(prop_val)
                model_prop = cls._properties[prop_name]
                query_result = cls.query(model_prop==prop_val).fetch()
                
                if query_result:
                    msg = prop_name
                    msg = msg + " already exists"
                    result['status'] = False
                    result['message'] = msg
                    result['entity'] = query_result[0]
                    return result
        
        return result
    
    '''
        Init process of the value submitted by user
        1. Remove the while space before and after the value
        2. Set the value to None for empty string
    '''
    @staticmethod
    def init_prop_val(prop_val):
        if isinstance(prop_val, (str, unicode)):
            prop_val = prop_val.strip()
            
        if prop_val == "":
            prop_val = None
        
        return prop_val
    
    '''
        If the property is a Boolean type
        Covert the value based on the type
    '''
   
    @classmethod
    def _convert_bool_prop(cls, prop_name, model_rec, op_type):
        
        #defualt property that only set at the backend
        if prop_name == 'is_active':
            return True
        
        if op_type == 'upload':
            if prop_name in model_rec:
                prop_val = model_rec.get(prop_name)
                prop_val = cls.init_prop_val(prop_val).lower()
                if prop_val == 'true':
                    prop_val = True
                elif prop_val == 'false':
                    prop_val = False
            else:
                prop_val = None
        else:
            if prop_name in model_rec:
                prop_val = True
            else:
                prop_val = False
        return prop_val
    '''
        If the property is a number type such as int, float
        Convert the string based on the type
    '''
    @staticmethod
    def _convert_number_prop(prop_type, prop_val):
        num_convert_list = {
            'IntegerProperty':int, 
            'FloatProperty':float,
            }
        
        if prop_type in num_convert_list:
            if prop_val != None:
                prop_val = num_convert_list[prop_type](prop_val)
        
        return prop_val
    
    '''
        If the property is a datetime type
        Covert the string to the datetime value
    '''
    @staticmethod
    def _convert_datetime_prop(prop_type, prop_val, cur_user, op_type):
        dt_convert_list = {
            'DateProperty': '%d/%m/%Y',
            'DateTimeProperty': '%d/%m/%Y %H:%M',
            'TimeProperty': '%H:%M', 
            }
        
        if op_type == 'upload':
            dt_convert_list['DateProperty'] = '%m/%d/%y'
        
        if prop_type in dt_convert_list:
            if prop_val != None:
                
                #Make sure the time format is HH:MM:SS
                '''if prop_type == "TimeProperty" and prop_val.count(":") == 1:
                    prop_val = prop_val + ":00"
                logging.info(prop_val)
                '''
                
                prop_val = datetime.datetime.strptime(prop_val, dt_convert_list[prop_type])
                if prop_type == 'DateProperty':
                    prop_val = prop_val.date()
                elif prop_type == 'TimeProperty':
                    prop_val = prop_val.time()
                elif prop_type == 'DateTimeProperty':
                    #Convert localtime to UTC time
                    user_tz = cur_user.user_timezone
                    UTC = UserTimeZone(offset=0)
                    utc_tm = prop_val.replace(tzinfo=user_tz).astimezone(UTC)
                    
                    #Remove the timezone infomation as NDB does not accept it
                    '''utc_tm_str = utc_tm.strftime(dt_convert_list[prop_type]) 
                    prop_val = datetime.datetime.strptime(utc_tm_str, dt_convert_list[prop_type])
                    '''
                    prop_val = utc_tm.replace(tzinfo=None)
            
        return prop_val
        
    '''
        If the property is a geopoint type
        Convert the stirng into the geopt value
    '''
    @staticmethod
    def _convert_geopt_prop(prop_type, prop_val):
        if (prop_type == 'GeoPtProperty'):
            if prop_val != None:
                if isinstance(prop_val, (str, unicode)):
                    prop_val = ndb.GeoPt(prop_val)
                elif isinstance(prop_val, tuple):
                    prop_val = ndb.GeoPt(*prop_val)
        return prop_val    

    '''
        If the property has a repeated attribute
        Convert the string into a list
        The string value should be separated by ','
    '''
    @classmethod
    def _convert_repeat_prop(cls, prop_name, prop_val):
        if cls._properties[prop_name]._repeated == True:
            #print "converting repeat prop(%s) with %s" %(prop_name, prop_val)
            if prop_val == None:
                prop_val = []
            elif isinstance(prop_val, (str, unicode)):
                prop_val = prop_val.split(',')
            
            #for each value in the list, continue to break it down by ,
            result_list = []
            for each in prop_val:
                if each.find(',') != -1:
                    sub_list = each.split(',')
                    
                    for str_val in sub_list:
                        str_val = cls.init_prop_val(str_val)
                        if str_val != None:
                            result_list.append(str_val)
                else:
                    each = cls.init_prop_val(each)
                    if each != None:
                        result_list.append(each)
            
            prop_val = result_list
        return prop_val
    
    @classmethod
    def process_structured_prop(cls, prop_val):
        return prop_val
    
    @classmethod
    def _convert_structured_prop(cls, 
                               prop_name, 
                               prop_type, 
                               prop_val):
        
        if prop_val and prop_type == 'StructuredProperty':
            prop_model_cls = cls._properties[prop_name]._modelclass
            if cls._properties[prop_name]._repeated == True:
                prop_val_list = []
                
                for each in prop_val:
                    each = cls.init_prop_val(each)
                    if each != None:
                        new_val = prop_model_cls.process_structured_prop(each)
                        prop_val_list.append(new_val)
                prop_val = prop_val_list
            else:
                prop_val = prop_model_cls.process_structured_prop(prop_val)
        return prop_val
    
    '''
        Get the true value for a key property
        In the form the value is the id of key model entity
        The key need to be retrieved based on the id
    '''
    @classmethod    
    def convert_keyprop_by_id(cls, 
                              prop_name, 
                              prop_val):
        #Get the KeyProperty model class and the property that represent the display value
        key_model_cls, key_prop_name = _get_keyprop_attr(cls._properties[prop_name])
        key_model_prop = key_model_cls._properties[key_prop_name]
        key_entity = None
        result = {}
        result['status'] = True
        
        #If entity use a number id, convert the string to integer
        if (key_model_cls.is_number_id == True 
            and not isinstance(prop_val, (int, long))):
            if (prop_val.isdigit()):
                key_entity_id = int(prop_val)
            else:
                result['status'] = False
                result['message'] = "id for %s is not a number" %(prop_name)
                return result
                #return result
        else:
            key_entity_id = prop_val
        
        #Get the entity based on the id
        key_entity = key_model_cls.get_by_id(key_entity_id)
                        
        if key_entity:
            result['key'] = key_entity.key
        else:
            result['status'] = False
            result['message'] = "no such value (%s) for %s" %(prop_val, prop_name)
        return result 
    
    @classmethod
    def _convert_keyprop_list_by_id(cls, 
                              prop_name, 
                              prop_val):
        key_list = []
        result = {}
        result['status'] = True
        for each_id in prop_val:
            result = cls.convert_keyprop_by_id(prop_name, each_id)
            if result['status'] == True:
                key_list.append(result['key'])
            else:
                return result
        
        result['key'] = key_list
        return result
    
    '''
        Get the true value for a key property
        In the form the value is the display value of the keyproperty
        This will happen when uploading data
    '''
    @classmethod    
    def convert_keyprop_by_value(cls, 
                              prop_name, 
                              prop_val,
                              model_rec,
                              cur_user):
        #Get the KeyProperty model class and the property that represent the display value
        key_model_cls, key_prop_name = _get_keyprop_attr(cls._properties[prop_name])
        key_model_prop = key_model_cls._properties[key_prop_name]
        result = {}
        result['status'] = True
        user_business_group = None
        user_business_team = None
        
        logging.info(model_rec)
        tmp_result = cls._convert_key_data_to_prop('business_group', 
                                                   model_rec=model_rec, 
                                                   cur_user=cur_user, 
                                                   op_type=None)
        
        if tmp_result['status'] == True:
            user_business_group = tmp_result['key']   
            
        tmp_result = cls._convert_key_data_to_prop('business_team', 
                                                   model_rec=model_rec, 
                                                   cur_user=cur_user, 
                                                   op_type=None)
        
        
        
        if tmp_result['status'] == True:
            user_business_team = tmp_result['key']   
            

        cond_list = []
        if key_model_cls.unique_level >= config.GROUP_UNIQUE.unique_level:
            logging.info(key_model_cls.unique_level)
            if user_business_group == None:
                result['status'] = False
                result['message'] = 'group id is missing'
                return result
            else:
                cond_list.append(key_model_cls.business_group==user_business_group)
        
        if key_model_cls.unique_level >= config.TEAM_UNIQUE.unique_level:
            if user_business_team == None:
                result['status'] = False
                result['message'] = 'team id is missing'
                return result
            else:
                cond_list.append(key_model_cls.business_team==user_business_team)
        
        cond_list.append(key_model_prop==prop_val)
        logging.info(cond_list)
        query_result = key_model_cls._model_query(cond_list=cond_list, 
                                                 cur_user=cur_user)
        logging.info(query_result)
        
        if (len(query_result) > 1):
            result['status'] = False
            result['message'] = 'more than 1 key found for %s, please contact system admin!' %prop_name
        elif (len(query_result) == 0):
            result['status'] = False
            result['message'] = '%s does not exist!' %prop_name
        else:
            result['key'] = query_result[0].key
        return result
    
    @classmethod
    def get_entity_id_by_value(cls, 
                              prop_name, 
                              prop_val,
                              model_rec,
                              cur_user):
        result = cls.convert_keyprop_by_value(prop_name, 
                                              prop_val, 
                                              model_rec, 
                                              cur_user)
        logging.info(result)
        if result['status'] == True:
            entity_id = result['key'].id()
        else:
            entity_id = None
        return entity_id
              
    @classmethod
    def _convert_keyprop_list_by_value(cls, 
                              prop_name, 
                              prop_val,
                              model_rec,
                              cur_user):
        key_list = []
        result = {}
        result['status'] = True
                
        for each_val in prop_val:
            result = cls.convert_keyprop_by_value(prop_name, 
                                                  each_val,
                                                  model_rec=model_rec,
                                                  cur_user=cur_user)
            if result['status'] == True:
                key_list.append(result['key'])
            else:
                return result
        
        result['key'] = key_list
        return result    

    @classmethod
    def _convert_key_prop(cls, 
                         prop_name,
                         prop_type, 
                         prop_val, 
                         model_rec,
                         cur_user,
                         op_type=None):
        '''
            For upload action, the key property is not 
            the id but the display value of the property
        '''
        result = {}
        '''
            If it's already a key, no addition handling is required.
            For internal operation, such as default user and group,
            This approach will be used.
        '''
        if isinstance(prop_val, ndb.Key):
            result['status'] = True
            result['key'] = prop_val
        else:
            is_list = isinstance(prop_val,list)
            if op_type == 'upload':
                if is_list:
                    result = cls._convert_keyprop_list_by_value(prop_name, 
                                                               prop_val, 
                                                               model_rec=model_rec,
                                                               cur_user=cur_user)
                else:
                    result = cls.convert_keyprop_by_value(prop_name, 
                                                      prop_val,
                                                      model_rec=model_rec,
                                                      cur_user=cur_user)
            else:
                if is_list:
                    result = cls._convert_keyprop_list_by_id(prop_name, prop_val)
                else:
                    result = cls.convert_keyprop_by_id(prop_name, prop_val)
        return result
            
    @classmethod
    def _convert_key_data_to_prop(cls,
                              prop_name,
                              model_rec,
                              cur_user,
                              op_type):
    
        prop_val = model_rec.get(prop_name)
        prop_type = cls._properties[prop_name].__class__.__name__
        prop_val = cls.init_prop_val(prop_val)
        prop_val = cls._convert_number_prop(prop_type, prop_val)
        prop_val = cls._convert_repeat_prop(prop_name, prop_val)
        prop_val = cls._convert_structured_prop(prop_name, prop_type, prop_val)                    
        
        '''
            If the property value is not None and is a key property
            In the form the value is the id of key model entity
            The key need to be retrieved based on the id
        '''
        if (prop_val != None 
            and prop_type == 'KeyProperty'):
                    
            '''
            For upload action, the key property is not 
            the id but the display value of the property
            '''
            result = cls._convert_key_prop(prop_name, 
                                           prop_type, 
                                           prop_val, 
                                           op_type=op_type,
                                           model_rec=model_rec,
                                           cur_user=cur_user)
 
            return result
    '''
        Method to retrieve data based on the model definition
        the return data is dictionary in which
        property name is the key
    '''
    @classmethod
    def get_data_from_rec(cls, 
                          model_rec, 
                          op_type=None,
                          cur_user=None):
        result = {}
        result['status'] = True
        result['message'] = ''
        prop_data = {}
        #print ("model_rec:%s" %model_rec)
        #Go through the ndb model property name
        for prop_name in cls._properties:
            
            prop_type = cls._properties[prop_name].__class__.__name__

            #Handle the boolean property            
            if prop_type == 'BooleanProperty':
                prop_val = cls._convert_bool_prop(prop_name=prop_name,
                                                  model_rec=model_rec,
                                                  op_type=op_type)
                prop_data[prop_name] = prop_val
            #If the property name is in record
            elif prop_name in model_rec:
                #Get the property value and type
                prop_val = model_rec.get(prop_name)
                
                prop_val = cls.init_prop_val(prop_val)
                prop_val = cls._convert_number_prop(prop_type, prop_val)
                prop_val = cls._convert_datetime_prop(prop_type, prop_val, cur_user, op_type)
                prop_val = cls._convert_geopt_prop(prop_type, prop_val)
                prop_val = cls._convert_repeat_prop(prop_name, prop_val)
                prop_val = cls._convert_structured_prop(prop_name, prop_type, prop_val)                    
                '''
                If the property value is not None and is a key property
                In the form the value is the id of key model entity
                The key need to be retrieved based on the id
                '''
                if (prop_val != None 
                    and prop_type == 'KeyProperty'):
                    
                    '''
                        For upload action, the key property is not 
                        the id but the display value of the property
                    '''
                    result = cls._convert_key_prop(prop_name, 
                                                  prop_type, 
                                                  prop_val, 
                                                  op_type=op_type,
                                                  model_rec=model_rec,
                                                  cur_user=cur_user)
 
                    if result['status'] == False:
                        return result
                    else:
                        prop_val = result['key']
                        del result['key']
                
                prop_data[prop_name] = prop_val
        
        result['data'] = prop_data
        return result
    
    '''
        method to check if the entity is 
        the key for other model class.
        usually used before deleting an entity
        the entity can only be deleted when is false.
    '''
    def _is_key_for(self, check_existing_key=None):
        result = {}
        result['status'] = True
        
        if check_existing_key == None:
            return result
        else:
            for each in check_existing_key:
                other_model_cls = each['model_cls']
                other_prop = each['other_prop']

                query_result = other_model_cls.query(other_prop==self.key).get()
                if query_result != None:
                    result['status'] = False
                    result['message'] = 'please remove all %s in this %s first!' %(each['model_display_name'], self.model_display_name)
                    return result
        return result
    
    @classmethod
    def get_id_from_rec(cls, model_rec, id_name=None):
        result = {}
        result['status'] = True
        result['message'] = ""
        
        #default id name from submitted form is _entity_id
        if id_name == None:
            id_name = '_entity_id'
        
        unique_id = model_rec.get(id_name)

        if unique_id == None:
            result['status'] = False
            result['message'] = 'record id does not exist'              
        elif cls.is_number_id == True and not isinstance(unique_id, (int, long)):
            if unique_id.isdigit():
                result['id'] = int(unique_id)
            else:
                result['status'] = False
                result['message'] = 'invalid record id format'
        else:
            result['id'] = unique_id
        return result
    
    @classmethod
    def get_form_fields(cls, 
                        include_list=None, 
                        exclude_list=None,
                        cur_user=None):
        
        #Get form definition for the model
        field_list = FormField.query_kind_dict(kind_name=cls.__name__, 
                                               cur_user=cur_user)
        #print field_list
        result_list = []

        for field in field_list:
            prop_name = field['prop_name']
            
            if include_list and prop_name not in include_list:
                continue
            
            if exclude_list and prop_name in exclude_list:
                continue
            
            if prop_name != '_entity_id':
                if cls._properties[prop_name]._repeated:
                    if field['create_attr']:
                        field['create_attr'] += " repeated"
                    else:
                        field['create_attr'] = "repeated"
                        
                    if field['edit_attr']:
                        field['edit_attr'] += " repeated"
                    else:
                        field['edit_attr'] = "repeated"   
                                        
                prop_type = cls._properties[prop_name].__class__.__name__
                if cls._properties[prop_name]._required:
                    if field['create_attr']:
                        field['create_attr'] += " required"
                    else:
                        field['create_attr'] = "required"
                        
                    if field['edit_attr']:
                        field['edit_attr'] += " required"
                    else:
                        field['edit_attr'] = "required"                        
                 
                if cls._properties[prop_name]._default:
                    field['default_value'] = cls._properties[prop_name]._default
                                         
                if cls._properties[prop_name]._choices:
                    field['choices'] = cls._properties[prop_name]._choices
                    if cls._properties[prop_name]._verbose_name:
                        field['choices'] = cls._properties[prop_name]._verbose_name.split(',')
                    #print field['choices']
                
                if prop_type == 'KeyProperty':
                    key_model_cls, key_prop_name = _get_keyprop_attr(cls._properties[prop_name]) 
                    field['choices'] = key_model_cls.get_prop_id_list(key_prop_name, 
                                                                      cur_user=cur_user)
                                                                      
                
                if cls._properties[prop_name]._verbose_name:
                    field['verbose_name'] = cls._properties[prop_name]._verbose_name
            
            result_list.append(field)
                    
        return result_list
    
    #Query the key property represent value and corresponding entity id
    @classmethod
    def get_prop_id_list(cls, prop_name, 
                         cur_user=None,
                         cond_list=None):
        
        if cond_list == None:
            cond_list = []
        if cls.unique_level >= config.GROUP_UNIQUE.unique_level:
            if cur_user.business_group == None:
                msg = 'group id is missing'
                logging.error('get_prop_id_list: %s' %msg)
            else:
                cond_list.append(cls.business_group==cur_user.business_group)
        
        if cls.unique_level >= config.TEAM_UNIQUE.unique_level:
            if cur_user.business_team == None:
                if hasattr(cur_user, "fake_business_team"):
                    fake_business_team = getattr(cur_user, "fake_business_team")
                    cond_list.append(cls.business_team==fake_business_team)
                else:
                    msg = 'team id is missing'
                    logging.error('get_prop_id_list: %s' %msg)
            else:
                cond_list.append(cls.business_team==cur_user.business_team)
        
        model_prop = cls._properties[prop_name]
        order_list = [model_prop]
        
        query_list = cls.query_data_to_dict(cur_user=cur_user,
                                            cond_list=cond_list,
                                            order_list=order_list)
        
        #print cls.__name__
        #print cond_list
        result_list = []
        for each in query_list:
            tmp_obj = {}
            #text value of the entity
            tmp_obj['text'] = each[prop_name]
            
            #id of the entity
            tmp_obj['_entity_id'] = each['_entity_id']
            #result_list.append(each[prop_name])
            result_list.append(tmp_obj)
        return result_list    
    
    @classmethod
    def prepare_create_data(cls, model_rec,                             
                            unique_id=None, 
                            is_unique=True,
                            op_type=None,
                            cur_user=None):
        return model_rec
        
    @classmethod
   
    def create_model_entity(cls, model_rec, 
                            unique_id=None, 
                            is_unique=True,
                            op_type=None,
                            cur_user=None):
        
        #print ("model_rec:%s" %model_rec)
        if (unique_id == None) and (cls.is_number_id == True):
            unique_id = cls.allocate_ids(1)[0]

        check_result = {}
        check_result['status'] = True
        check_result['message'] = ""
        check_result['entity'] = None
        exist_entity = None
        model_rec = cls.prepare_create_data(model_rec=model_rec, 
                                            unique_id=unique_id, 
                                            is_unique=is_unique,
                                            op_type=op_type,
                                            cur_user=cur_user)
                
        #check if the rec value is unique
        check_result = cls.check_unique_value(model_rec=model_rec, 
                                              cur_user=cur_user,
                                              op_type=op_type)
        
        
        if is_unique == True:
            if check_result['status'] != True:
                check_result['message'] = "Cannot create new %s record because the value for %s" %(cls.model_display_name, check_result['message'])
                return check_result
        else:
            if check_result['status'] !=True:
                check_result['status'] = True
                exist_entity = check_result['entity']
                
        #check if the id is unique
        tmp_entity = cls.get_by_id(unique_id)
        if tmp_entity:
            check_result['status'] = False
            check_result['message'] = 'Cannot create new %s record because the id already exists' %(cls.model_display_name)
            check_result['entity'] = tmp_entity
        else:
            tmp_entity = cls(id=unique_id)
            
            #Replace the existing entity with the same ID
            if cls.is_replaced == True and exist_entity:
                tmp_entity = exist_entity
            
            result = tmp_entity.get_data_from_rec(model_rec=model_rec, 
                                                  op_type=op_type,
                                                  cur_user=cur_user)
            #check if there is error when getting the data
            if result['status'] != True:
                check_result['status'] = False
                check_result['message'] = 'Cannot create new %s because %s' %(cls.model_display_name, result['message'])
            else:
                entity_data = result['data']
                tmp_entity.populate(**entity_data)
                tmp_entity.put()
                check_result['message'] = "The %s record is created successfully!" %(cls.model_display_name)
                check_result['entity'] = tmp_entity
                
                
        return check_result            

    @classmethod
    def prepare_update_data(cls, model_rec,                             
                            unique_id=None, 
                            is_unique=True,
                            cur_user=None):
        return model_rec
        
    @classmethod
    @ExpHandleAll()        
    def update_model_entity(cls, model_rec, 
                            unique_id=None, 
                            is_unique=True, 
                            id_name=None, 
                            cur_user=None):
        result = {}
        result['status'] = True
        result['message'] = ""
        
        model_rec = cls.prepare_update_data(model_rec=model_rec, 
                                            unique_id=unique_id, 
                                            is_unique=is_unique,
                                            cur_user=cur_user)               
        
        #if unique_id is not defined, get it from the record
        if unique_id == None:
            result = cls.get_id_from_rec(model_rec, id_name=id_name)
            if result['status'] != True:
                result['message'] = "Update failed, %s." %result['message']
                return result
            else:
                unique_id = result['id']
                del result['id']
        
        #Get the entity based on id
        
        model_entity = cls.get_by_id(unique_id)
        #print ("unique id: %s %s" %(unique_id, type(unique_id)))
        #if entity does not exist, report the error
        if model_entity == None:
            result['status'] = False
            result['message'] = "Update failed, the record does not exist!"
            return result
        #check if the rec value is unique
        elif is_unique == True:
            check_result = cls.check_unique_value(model_rec, 
                                                  cur_user=cur_user)
            if check_result['status'] != True:
                tmp_entity = check_result['entity']
                if tmp_entity.key != model_entity.key:
                    result['status'] = False
                    result['message'] = "Update failed, %s." %check_result['message']
                    return result
            
        result = model_entity.get_data_from_rec(model_rec, 
                                                cur_user=cur_user)
        #check if there is error when getting the data
        if result['status'] != True:
            result['message'] = 'Cannot update %s because %s' %(cls.model_display_name, result['message'])
            return result
        else:
            entity_data = result['data']
            model_entity.populate(**entity_data)
            model_entity.put()
            result['message'] = "The %s record is updated successfully!" %(cls.model_display_name)
            result['entity'] = model_entity
        return result

    '''
        method to prepare the dictionary for checking if 
        the entity is key for other records
    '''
    @classmethod
    def prepare_check_key(cls):
        return None
    
    @classmethod
    @ExpHandleAll()
    def delete_model_entity(cls, model_rec, unique_id=None, 
                            is_unique=True, id_name=None):
        result = {}
        result['status'] = True
        result['message'] = ""
        check_existing_key = cls.prepare_check_key()
        #if unique_id is not defined, get it from the record
        if unique_id == None:
            result = cls.get_id_from_rec(model_rec, id_name)
            
            if result['status'] != True:
                result['message'] = "Delete failed, %s." %result['message']
                return result
            else:
                unique_id = result['id']
                del result['id']
        
        model_entity = cls.get_by_id(unique_id)
        
        if model_entity == None:
            result['status'] = False
            result['message'] = "Delete failed, the record does not exist!" 
            return result
        else:
            result = model_entity._is_key_for(check_existing_key)
            
            #The entity is key for other records, cannot delete
            if result['status'] == True:
                result['entity'] = model_entity
                model_entity.key.delete()
                #Set the flag is_active to False
                #model_entity.is_active = False
                #model_entity.put()
                result['message'] = "The %s record has been deleted" %(cls.model_display_name)
        return result
        
class FormField(BaseModel):
    input_type_list = ['button', 'checkbox', 'color', 'date', 'datetime', 'datetime-local', 
                       'email', 'month', 'number', 'password', 'radio', 'range', 'reset', 
                       'search', 'search', 'submit', 'tel', 'text', 'time', 'url', 'week']
    kind_name = ndb.StringProperty(required=True)
    prop_name = ndb.StringProperty(required=True)
    label = ndb.StringProperty(required=True, indexed=False)
    form_seq = ndb.IntegerProperty(required=True)
    create_attr = ndb.StringProperty(indexed=False)
    edit_attr = ndb.StringProperty(indexed=False)
    table_attr = ndb.StringProperty(indexed=False)
    input_name = ndb.StringProperty(indexed=False, required=True, default='input', choices=['input', 'select-multiple', 'select', 'textarea'], verbose_name=','.join(['input', 'select-multiple', 'select', 'textarea']))
    input_type = ndb.StringProperty(indexed=False, required=True, default='text', choices=input_type_list, verbose_name=','.join(input_type_list))
    place_holder = ndb.StringProperty(indexed=False)
    data_error = ndb.StringProperty(indexed=False)    
    other_attr = ndb.StringProperty(indexed=False)
    default_value = ndb.StringProperty(indexed=False)
    
    model_display_name = 'form field'
    unique_and_props = ['kind_name', 'prop_name']
    is_number_id = False
    
    @classmethod
    def query_kind_dict(cls, kind_name, cur_user):
        cond_list = [cls.kind_name==kind_name]
        order_list = [cls.form_seq]
        is_with_entity_id = False
        result_list = cls.query_data_to_dict(cond_list=cond_list, 
                                             order_list=order_list, 
                                             is_with_entity_id=is_with_entity_id, 
                                             cur_user=cur_user)
        return result_list    
    
    @classmethod
    def prepare_query_order(cls, order_list):
        if order_list == None:
            order_list = [cls.kind_name, cls.form_seq]
        return order_list
        
    @classmethod
    @ExpHandleAll() 
    def create_model_entity(cls, model_rec, 
                            op_type=None,
                            cur_user=None):
        unique_id = model_rec.get('kind_name')+"."+model_rec.get('prop_name')
        return super(FormField, cls).create_model_entity(model_rec=model_rec, unique_id=unique_id)
