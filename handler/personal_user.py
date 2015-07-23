from model.account import UserRole, BusinessGroup
from utils.ndb_utils import *
from utils.handler_utils import *
from handler.base import CRUDHandler

from model.account import User
import config

class PersonalUserHandler(CRUDHandler):
    @webapp2.cached_property
    def access_level(self):
        user_role = UserRole.query(UserRole.role_name == 'Personal User').get()
        return user_role.access_level
    
class UserProfileHandler(PersonalUserHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'User Profile'
        super(UserProfileHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/user/user_profile'
        self.form['dt_source'] = 'User'
        self.model_cls = get_kind_by_name(self.form['dt_source'])  
        self.number_id = True
        self.edit_include_list = ['email', 'user_name', 'created']
        
    def get(self):
        model_entity = self.user
        self.get_edit(model_entity)
        
    def async_edit(self):
        self.request.POST['user_access_level'] = self.user.access_level
        super(UserProfileHandler, self).async_edit()         
        
class ChangePasswordHandler(PersonalUserHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'Password'
        super(ChangePasswordHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/user/change_password'
        self.number_id = True        
        
    def get(self):
        self.render('change_password.html', form=self.form)
        
    def post(self):
        password = self.request.get('password')
        if not password or password != self.request.get('confirm_password'):
            self.async_render_msg(False, "Password does not match!")
            return
        self.user.set_password(password)
        self.user.put()
        self.async_render_msg(True, "Your password has been changed!")
        
class ChangePricePlanHandler(PersonalUserHandler):
    def __init__(self, *arg, **kwargs):
        self.page_name = 'price plan'
        super(ChangePricePlanHandler, self).__init__(*arg, **kwargs)
        self.form['action'] = '/user/change_priceplan'
        self.form['dt_source'] = 'PricePlan'
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
], config=config.WSGI_CONFIG, debug=config.DEBUG)         
    
    