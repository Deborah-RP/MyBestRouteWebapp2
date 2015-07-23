import webapp2
import logging
import time

from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models
from webapp2_extras import security

from base_model import BaseModel
from config import DEBUG
from utils.exception_utils import * 
from utils.ndb_utils import *

APP_USERS = ['super_admin', 'acct_admin', 'member']
USER_STATUS = ['Pending', 'Active', 'Terminated', 'Failed Login Locked', 'Admin Locked']

'''
class for Price Plan
the plan name is the id which should be unique
'''
class PricePlan(BaseModel):
    plan_name = ndb.StringProperty(required=True)
    plan_type = ndb.StringProperty(required=True, choices=['Personal', 'Business'])
    plan_price = ndb.FloatProperty(required=True, default=0.0)
    description = ndb.StringProperty(indexed=False)
    max_user_per_group = ndb.IntegerProperty(required=True, indexed=False)
    max_route_per_group =ndb.IntegerProperty(required=True, indexed=False)
    max_loc_per_route = ndb.IntegerProperty(required=True, indexed=False)
    plan_created = ndb.DateTimeProperty(auto_now_add=True)
    plan_updated = ndb.DateTimeProperty(auto_now=True)
    
    model_name = 'price plan'
    unique_or_props = ['plan_name'] 
    number_id = True   
    
    @classmethod
    def query_all(cls):
        return cls.query().order(cls.plan_type, cls.plan_price)
    
    @classmethod
    def query_all_dict(cls, cond_list=None):
        order_list = [cls.plan_type, cls.plan_price]
        return super(PricePlan, cls).query_all_dict(order_list, cond_list)
'''
class for Account (business or personal)
a numeric key id will be generated for the account
'''
class BusinessGroup(BaseModel):
    business_name = ndb.StringProperty(required=True)
    price_plan = ndb.KeyProperty(required=True, kind=PricePlan, verbose_name='plan_name')
    status = ndb.StringProperty(required=True, default=USER_STATUS[0], choices=USER_STATUS)
    country = ndb.StringProperty(required=True, verbose_name="country_option")
    timezone = ndb.StringProperty(required=True, verbose_name="timezone_option")
    expiry_date = ndb.DateProperty(indexed=False)
    group_created = ndb.DateTimeProperty(auto_now_add=True)
    group_updated = ndb.DateTimeProperty(auto_now=True)
    paypal_id = ndb.StringProperty(indexed=False)    
    last_payment = ndb.DateProperty(indexed=False)

    unique_or_props = ['business_name']
    model_name = 'business group'
    number_id = True
    
    @classmethod
    def query_all(cls):
        return cls.query().order(cls.price_plan, cls.business_name)
    
    @classmethod
    def query_all_dict(cls, cond_list=None):
        order_list = [cls.price_plan, cls.business_name]
        return super(BusinessGroup, cls).query_all_dict(order_list, cond_list)

'''
class for UserRole
For security control
'''
class UserRole(BaseModel):
    role_name = ndb.StringProperty(required=True)
    access_level = ndb.IntegerProperty(required=True, default=1)
    description = ndb.TextProperty(indexed=False)
    unique_or_props = ['role_name']   
    model_name = 'user role'
    number_id = True
    
    @classmethod
    def query_all(cls):
        return cls.query().order(-cls.access_level)
    
    @classmethod
    def query_all_dict(cls, cond_list=None):
        order_list = [-cls.access_level]
        return super(UserRole, cls).query_all_dict(order_list, cond_list)    

'''
class for User, which extends the default webapp2 User model
https://webapp-improved.appspot.com/api/webapp2_extras/appengine/auth/models.html
It has the below params:
    - created
    - updated
    - auth_ids
    - password
Its parent is BusinessGroup
login id is email
'''
class User(BaseModel, webapp2_extras.appengine.auth.models.User):
    email = ndb.StringProperty(required=True)
    email_lower = ndb.ComputedProperty(lambda self: self.email.lower())
    user_role = ndb.KeyProperty(kind=UserRole, required=True, verbose_name='role_name')
    access_level = ndb.ComputedProperty(lambda self: self.user_role.get().access_level)
    business_group = ndb.KeyProperty(kind=BusinessGroup, verbose_name='business_name')
    price_plan = ndb.KeyProperty(kind=PricePlan, verbose_name='plan_name')
    user_name = ndb.StringProperty(required=True)
    status = ndb.StringProperty(default=USER_STATUS[0], choices=USER_STATUS)
    last_login_time = ndb.DateTimeProperty(indexed=False)
    last_failed_login = ndb.DateTimeProperty(indexed=False)
    failed_login_count = ndb.IntegerProperty(indexed=False, default=0)
    last_host_address = ndb.StringProperty(indexed=False)
    
    unique_or_props = ['email_lower']   
    model_name = 'user'
    number_id = True
    
    '''
    @property
    def access_level(self):
        user_role = self.user_role.get()
        return user_role.access_level
    '''    
    @classmethod
    def query_all(cls):
        return cls.query().order(cls.business_group, cls.user_role, cls.email_lower)
    
    @classmethod
    def query_all_dict(cls, cond_list=None):
        order_list = [cls.access_level, cls.business_group, cls.email_lower]
        return super(User, cls).query_all_dict(order_list, cond_list)
    
    def set_password(self, raw_password):
        '''Sets the password for the current user
        :param raw_password:
        The raw password which will be hashed and stored
        '''
        self.password = security.generate_password_hash(raw_password, length=12)
        
    @classmethod
    def get_by_auth_token(cls, user_id, token, subject='auth'):
        """Returns a user object based on a user ID and token.
        :param user_id:
        The user_id of the requesting user.
        :param token:
        The token string to be verified.
        :returns:
        A tuple ``(User, timestamp)``, with a user object and
        the token timestamp, or ``(None, None)`` if both were not found.
        """
        token_key = cls.token_model.get_key(user_id, subject, token)
        user_key = ndb.Key(cls, user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = ndb.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp
        
        return None, None
    
    @staticmethod
    def check_user_data(data):
        #print "User data is %s" %model_rec
        '''
        role_id = model_rec['user_role']
        if is_number(role_id):
            role_id = int(role_id)
        else:
            msg = "Please choose a user role."
            return False, msg
        '''
        
        role_key = data['user_role']
        if not role_key:
            msg = "Please choose a user role."
            return False, msg
        
        #user_role = UserRole.get_by_id(role_id)
        user_role = role_key.get()
        
        if user_role.access_level > data['user_access_level']:
            msg = "You are not allowed to use this user role."
            return False, msg
        else:
            del data['user_access_level']
        
        if role_key == UserRole.query(UserRole.role_name=='Personal User').get().key:
            if 'business_group' in data:
                data['business_group'] = None
                
            #check price plan
            if 'price_plan' not in data:
                price_plan = None
            else:
                plan_key = data['price_plan']
                if not plan_key:
                    msg = "Please choose a price plan!"
                    return False, msg
                
                price_plan = plan_key.get()
                if price_plan.plan_type != "Personal":
                    msg = "Please choose a personal plan"
                    return False, msg
        else:
            if 'price_plan' in data:
                data['price_plan'] = None
            
            #check business group
            if 'business_group' not in data:
                business_group = None
            else:
                business_key = data['business_group']
                if not business_key:
                    msg = "Please choose a business group!"
                    return False, msg
        return True, None
    
    @classmethod
    def create_model_entity(cls, model_rec):
        '''
        Create a new user from the request data
        :param model_rec
            A request object or dictionary
        '''
        email_lower = model_rec.get('email').lower()
        model_entity = cls(id=email_lower)
        
        if 'user_role' not in model_rec:
            model_rec['user_role'] = UserRole.query(UserRole.role_name=="Personal User").get().key.id()
            
        if 'user_status' not in model_rec:
            model_rec['status'] = "Pending"
        
        if 'price_plan' not in model_rec:
            model_rec['price_plan'] = PricePlan.query(PricePlan.plan_name=='Personal Free Plan').get().key.id()
        
        data = model_entity.get_data_from_post(model_rec)
        data['user_access_level'] = model_rec['user_access_level']
        status, msg = cls.check_user_data(data)
        print ("model_rec %s data %s" %(model_rec, data))
        if not status:
            return status, msg
        
        if 'password' in data:
            data['password_raw'] = data['password']
            del data['password']
        else:
            data['password_raw'] = ""
        
        data['verified'] = False

        if DEBUG:
            logging.info("The user data is")
            logging.info(data)

        user_data = cls.create_user(email_lower, None, **data)
        if not user_data[0]: 
            msg = 'Unable to create user because email already exists.'
            return False, msg
        else:
            return True, user_data
        
    @classmethod
    def update_model_entity(cls, model_rec, number_id=False):
        status, msg = cls.check_user_data(model_rec)
        if not status:
            
            return status, msg
        else:
            return super(User, cls).update_model_entity(model_rec, number_id)
        
    @classmethod
    def del_model_entity(cls, model_rec, number_id=False):
        unique_id = cls.get_id_from_post(model_rec, number_id)
        tmp_entity = cls.get_by_id(unique_id)
        
        if not tmp_entity:
            return False, "No such user account!"
        else:
            tmp_entity.status = "Terminated"
            tmp_entity.put()
            return True, "The user account has been terminated!"
            
