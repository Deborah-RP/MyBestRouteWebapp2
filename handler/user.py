import config

from handler.base import CRUDHandler
from handler.auth import AuthHandler
from model.account import UserRole


class UserHandler(CRUDHandler, AuthHandler):
    def get_access_level(self, user_role_name):
        user_role = UserRole.query(UserRole.role_name == user_role_name).get()
        return user_role.access_level        
    
    #By default, it shows all users
    def init_form_data(self):
        self.max_user_level = self.get_access_level(config.SUPER_ADMIN)
        self.min_user_level = self.get_access_level(config.TEAM_USER)
        
    def process_get_form_data(self, form_data):
        for field in form_data['field_list']:
            #option for role exclude those access level higher than current user
            if field['prop_name'] == 'user_role':
                idx = 0
                while idx < len(field['choices']):
                    user_role = UserRole.get_by_id(field['choices'][idx]['_entity_id'])
                    if (user_role.access_level > self.user.access_level 
                        or user_role.access_level < self.min_user_level 
                        or user_role.access_level > self.max_user_level):
                        #remove the option by index
                        field['choices'].pop(idx)
                    else:
                        idx +=1
        return form_data    
        
    def async_create(self):
        response = self.create_new_user(config.NEW_USER_VERIFICATION)
        self.async_render_msg(response)
        
    def async_edit(self):
        self.request.POST['user_access_level'] = self.user.access_level
        super(UserHandler, self).async_edit()

    def async_query_all_json(self, cond_list=None):
        if cond_list:
            cond_list.append(self.model_cls.access_level <= self.user.access_level)
            cond_list.append(self.model_cls.access_level >= self.min_user_level)
            cond_list.append(self.model_cls.access_level <= self.max_user_level)
        else:
            cond_list = [self.model_cls.access_level <= self.user.access_level, 
                     self.model_cls.access_level >= self.min_user_level,
                     self.model_cls.access_level <= self.max_user_level]
        super(UserHandler, self).async_query_all_json(cond_list=cond_list)
        
    def async_upload(self):
        response = {}
        response['status'] = True
        response['message'] = "Batch upload for user account is not allowed!"
        self.async_render_msg(response)        