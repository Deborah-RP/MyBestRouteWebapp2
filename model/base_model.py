from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
import logging
from datetime import datetime

from config import DEBUG
from utils.exception_utils import ExpHandleAll
from utils.ndb_utils import *


class BaseModel(ndb.Model):
    unique_or_props = []
    unique_and_props = []
    
    @staticmethod
    def query_to_dict(result_list):
        data_list = []
        for each in result_list:
            data_list.append(each.to_dict())
        return data_list
    
    #only used when init the datastore
    @classmethod
    def _init_form_field(cls):
        for prop in cls._properties:
            unique_id = cls.__name__ + '.' + prop
            if FormField.get_by_id(unique_id):
                continue
            new_field = FormField(id=unique_id)
            new_field.kind_name = cls.__name__
            new_field.prop_name = prop
            new_field.label = prop
            new_field.order = -1
            new_field.input_name = 'input'
            new_field.input_type = 'text'
            new_field.put()


        unique_id = cls.__name__ + '._entity_id'
        new_field = FormField(id=unique_id)
        new_field.kind_name = cls.__name__
        new_field.prop_name = '_entity_id'
        new_field.label = 'Entity ID'
        new_field.order = 1
        new_field.input_name = 'input'
        new_field.input_type = 'text'
        new_field.create_attr = 'hidden'
        new_field.edit_attr = 'readonly'
        new_field.put()        
    
    def to_dict(self):
        key_dict = {}
        dt_list = []
        for prop in self._properties:
            prop_type = self._properties[prop].__class__.__name__
            if prop_type == 'KeyProperty':
                key_dict[prop] = self._properties[prop]._verbose_name
            elif prop_type in ['DateTimeProperty', 'TimeProperty', 'DateProperty']:
                dt_list.append(prop)
        
        tmp_obj = super(BaseModel, self).to_dict()
        for prop in key_dict:
            #get the other entity based on key
            key_val = getattr(self, prop)
            if key_val:
                model_entity = key_val.get()
                other_prop_name = key_dict[prop]
            #get the display name of the KeyProperty
                tmp_obj[prop] = getattr(model_entity, other_prop_name)
            
        for prop in dt_list:
            if tmp_obj[prop]:
                
                dt_obj = getattr(self, prop)
                tmp_obj[prop] = dt_obj.isoformat() 
            
        return tmp_obj
        
    @classmethod
    def query_all_dict(cls, order_list=None, cond_list=None):
        if cond_list:
            query_result = cls.query(*cond_list)
        else:
            query_result = cls.query()
        
        if order_list:
            result_list = query_result.order(*order_list).fetch()
        else:
            result_list = query_result.fetch()
            
        data_list = []
        for each in result_list:
            tmp_obj = each.entity_to_dict()
            data_list.append(tmp_obj)
        return data_list
    
    def entity_to_dict(self):
        tmp_obj = self.to_dict()
        tmp_obj['_entity_id'] = self.key.id()
        return tmp_obj
    
    @classmethod
    def get_prop_id_list(cls, prop_name):
        query_list = cls.query_all_dict()
        result_list = []
        for each in query_list:
            tmp_obj = {}
            tmp_obj['text'] = each[prop_name]
            tmp_obj['_entity_id'] = each['_entity_id']
            #result_list.append(each[prop_name])
            result_list.append(tmp_obj)
        return result_list

    @classmethod
    def get_form_fields(cls, include_list=None, exclude_list=None):
        field_list = FormField.query_kind_dict(cls.__name__)
        result_list = []

        for field in field_list:
            prop = field['prop_name']
            
            if include_list and prop not in include_list:
                continue
            
            if exclude_list and prop in exclude_list:
                continue
                
            if prop != '_entity_id':
                prop_type = cls._properties[prop].__class__.__name__
                if cls._properties[prop]._required:
                    if field['create_attr']:
                        field['create_attr'] += " required"
                    else:
                        field['create_attr'] = "required"
                        
                    if field['edit_attr']:
                        field['edit_attr'] += " required"
                    else:
                        field['edit_attr'] = "required"                        
                 
                if cls._properties[prop]._choices:
                    field['choices'] = cls._properties[prop]._choices
                        #print field['choices']
                
                if prop_type == 'KeyProperty':
                    model_cls, v_name = get_key_prop_val(cls._properties[prop]) 
                    field['choices'] = model_cls.get_prop_id_list(v_name)
                
                if cls._properties[prop]._verbose_name:
                    field['verbose_name'] = cls._properties[prop]._verbose_name
            
            result_list.append(field)
                    
        if DEBUG:
            logging.info("The field list is %s" %field_list)
                       
        return result_list     
    
    @classmethod
    def is_unique(cls, prop_name, prop_val):
        prop = cls._properties[prop_name]
        query_result = cls.query(prop==prop_val).fetch()
        if query_result:
            return False
        else:
            return True
    @classmethod
    def get_by_unique_vals(cls, model_rec):
        if len(cls.unique_and_props) > 0:
            and_query = cls.query()
            for prop_name in cls.unique_and_props:
                value = model_rec.get(prop_name)
                prop = cls._properties[prop_name]
                and_query = and_query.filter(prop==value)
                
            query_result = and_query.fetch()
            if query_result:
                msg = '+'.join(cls.unique_and_props)
                return query_result, msg
        
        #check entity with or condition
        if (len(cls.unique_or_props)):
            for prop_name in cls.unique_or_props:
                value = model_rec.get(prop_name)
                prop = cls._properties[prop_name]
                query_result = cls.query(prop==value).fetch()
                if query_result:
                    msg = prop_name
                    return query_result, msg
        
        return None, None
    
    @classmethod
    def get_unique_entity(cls, model_rec, unique_id):
        query_result, msg = cls.get_by_unique_vals(model_rec)
        if query_result:
            return query_result, msg

        tmp_entity = cls.get_by_id(unique_id)
        if tmp_entity:
            return tmp_entity, "id"
        else:
            return None, ""    
    
    @classmethod
    def create_unique_entity(cls, model_rec, unique_id):
        model_entity, msg = cls.get_unique_entity(model_rec, unique_id)
        if model_entity:
            msg = "Cannot create new record because the value for %s \
            is not unique" %msg
            return False, msg
        
        model_entity = cls(id=unique_id)
        data = model_entity.get_data_from_post(model_rec)
        model_entity.populate(**data)
        model_entity.put()
        return True, "The %s created successfully!" %(cls.model_name)
        
    @classmethod
    def update_unique_entity(cls, model_rec, unique_id):
        query_result, msg = cls.get_by_unique_vals(model_rec)
        model_entity = cls.get_by_id(unique_id)
        
        if query_result:
            tmp_entity = query_result[0]
            if len(query_result) > 1 or (tmp_entity.key != model_entity.key):
                msg = 'Update failed, the value for %s already exists!' %msg
                return False, msg
        
        if model_entity:
            data = model_entity.get_data_from_post(model_rec)
            model_entity.populate(**data)
            model_entity.put()
            return True, "The %s updated successfully!" %(cls.model_name)
        else:
            return False, "Update failed, the %s record cannot be found!" %(cls.model_name)
    
    #for model that use number id
    @classmethod
    @ExpHandleAll()        
    def create_model_entity(cls, model_rec):
        unique_id = cls.allocate_ids(1)[0]
        return cls.create_unique_entity(model_rec, unique_id)

    @classmethod
    @ExpHandleAll()        
    def update_model_entity(cls, model_rec, number_id=False):
        unique_id = cls.get_id_from_post(model_rec, number_id)
        return cls.update_unique_entity(model_rec, unique_id=unique_id)
    
    @classmethod
    def del_model_entity(cls, model_rec, number_id=False):
        if hasattr(cls, 'model_name'):
            model_name = cls.model_name
        else:
            model_name = ""
        
        unique_id = cls.get_id_from_post(model_rec, number_id)
        tmp_entity = cls.get_by_id(unique_id)
        
        if not tmp_entity:
            return False, "No such %s" %model_name
        else:
            tmp_entity.key.delete()
            return True, "The %s has been deleted!" %model_name
        
    @classmethod
    def get_id_from_post (cls, model_rec, number_id=False):  
        unique_id = model_rec.get('_entity_id')
        if (number_id):
            unique_id = int(unique_id)
        return unique_id
    
    def get_data_from_post(self, model_rec):
        prop_data = {}
        num_convert = {
         'IntegerProperty':int, 
         'FloatProperty':float,
        }
        dt_convert = {
        'DateProperty': '%Y-%m-%d',
        'DateTimeProperty': '%Y-%m-%d %H:%M:%S', 
        }
        
        for prop in self._properties:
            if prop in model_rec:
                prop_val = model_rec.get(prop)
                prop_type = self._properties[prop].__class__.__name__
                if prop_val =="" or prop_val == None:
                    prop_val = None
                elif (prop_type in num_convert):
                    prop_val = num_convert[prop_type](prop_val)
                elif(prop_type in dt_convert):
                    prop_val = datetime.strptime(prop_val, dt_convert[prop_type])
                    
                if prop_val and prop_type == 'KeyProperty':
                    model_cls, v_name = get_key_prop_val(self._properties[prop])
                    model_prop = model_cls._properties[v_name]
                    key_prop = None
                    if (model_cls.number_id and is_number(prop_val)):
                        _entity_id = int(prop_val)
                        key_prop = model_cls.get_by_id(_entity_id)
                    if key_prop:
                        prop_val = key_prop.key
                    else:
                        #For upload case, the value is text not entity id
                        key_prop = model_cls.query(model_prop==prop_val).get()
                        if key_prop:
                            prop_val = key_prop.key
                        else:
                            prop_val = None
                prop_data[prop] = prop_val
        return prop_data        
    
class FormField(BaseModel):
    kind_name = ndb.StringProperty(required=True)
    prop_name = ndb.StringProperty(required=True)
    label = ndb.StringProperty(required=True)
    order = ndb.IntegerProperty(required=True)
    create_attr = ndb.StringProperty(indexed=False)
    edit_attr = ndb.StringProperty(indexed=False)
    table_attr = ndb.StringProperty(indexed=False)
    input_name = ndb.StringProperty(indexed=False, choices=['input', 'select', 'textarea'])
    input_type = ndb.StringProperty(indexed=False, choices=['number', 'date', 'datetime-local', 'text', 'password', 'button', 'checkbox', 'email', 'hidden', 'submit', 'time'])
    place_holder = ndb.StringProperty(indexed=False)
    data_error = ndb.StringProperty(indexed=False)    
    rows = ndb.StringProperty(indexed=False)
    min = ndb.StringProperty(indexed=False)
    max = ndb.StringProperty(indexed=False)
    value = ndb.StringProperty(indexed=False)
    
    model_name = 'form field'
    unique_and_props = ['kind_name', 'prop_name']
    number_id = False
    
    @classmethod
    def query_kind_dict(cls, kind_name):
        data_list = cls.query(cls.kind_name==kind_name).order(cls.order).fetch()
        data_list = cls.query_to_dict(data_list)
        return data_list    

    @classmethod
    def query_all_dict(cls, cond_list=None):
        order_list = [cls.kind_name, cls.order]
        return super(FormField, cls).query_all_dict(order_list, cond_list)
        
    @classmethod
    def create_model_entity(cls, model_rec):
        unique_id = model_rec.get('kind_name')+"."+model_rec.get('prop_name')
        return cls.create_unique_entity(model_rec, unique_id)
