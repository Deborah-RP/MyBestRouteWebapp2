import webapp2
import config
import logging
from handler.base import CRUDHandler
from handler.auth import AuthHandler
from model.account import UserRole, BusinessGroup, BusinessTeam

#common handler for all the User CRUD
class UserHandler(CRUDHandler, AuthHandler):
    def get_access_level(self, user_role_name):
        user_role = UserRole.query(UserRole.role_name == user_role_name).get()
        return user_role.access_level        
    
    #By default, it shows all users
    def init_form_data(self):
        self.max_user_level = config.SUPER_ADMIN.access_level
        self.min_user_level = config.TEAM_USER.access_level
        
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
        result = self.create_new_user(config.NEW_USER_VERIFICATION)
        if result['status'] == True:
            rec_entity = result['entity']
            self.create_audit_log('Create', rec_entity)
        else:
            logging.info(result['message'])        
        self.async_render_msg(result)
        
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

class SuperAdminHandler(CRUDHandler):
    @webapp2.cached_property
    def min_access_level(self):
        #user_role = UserRole.query(UserRole.role_name == config.SUPER_ADMIN.role_name).get()
        return config.SUPER_ADMIN.access_level

    @webapp2.cached_property
    def business_group_id(self):
        return self.user.business_group.get().key.id()

    def post(self):
        self.request.POST['user_created'] = str(self.user.key.id())
        super(SuperAdminHandler, self).post()
        
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each['user_created'] = self.user.key
        return upload_data
    
class SysAdminHandler(SuperAdminHandler):
    @webapp2.cached_property
    def min_access_level(self):
        #user_role = UserRole.query(UserRole.role_name == config.SYS_ADMIN.role_name).get()
        return config.SYS_ADMIN.access_level
    
class GroupAdminHandler(CRUDHandler):
    @webapp2.cached_property
    def min_access_level(self):
        #user_role = UserRole.query(UserRole.role_name == config.GROUP_ADMIN.role_name).get()
        return config.GROUP_ADMIN.access_level
    
    @webapp2.cached_property
    def teams_in_group(self):
        teams_in_group = BusinessTeam.get_prop_id_list('team_name', 
                                                       cur_user=self.user)
        return teams_in_group
        
    @webapp2.cached_property
    def business_group_id(self):
        return self.user.business_group.get().key.id()    
    
    def process_get_form_data(self, form_data):
        if self.teams_in_group:
            form_data['teams_in_group'] = self.teams_in_group
        form_data = super(GroupAdminHandler, self).process_get_form_data(form_data)
        return form_data     
        
    def post(self):
        self.request.POST['user_created'] = str(self.user.key.id())
        self.request.POST['business_group'] = str(self.business_group_id)
        '''
        if self.is_team_unique == True:
            if 'business_team' not in self.model_cls.unique_and_props:
                self.model_cls.unique_and_props.append('business_team')
        '''
        super(GroupAdminHandler, self).post()
        
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each['user_created'] = self.user.key
            each['business_group'] = self.user.business_group
        return upload_data
    
    def set_default_country(self, form_data):
        field_list = form_data['field_list']
        for each in field_list:
            if each['prop_name'] == 'country':
                if self.user.business_group:
                    each['default_value'] = self.user.business_group.get().country
                else:
                    each['default_value'] = None
        return form_data
    
    def async_query_all_json(self, 
        cond_list=None, 
        order_list=None, 
        is_with_entity_id=True, 
        cur_user=None):
        cond_list = [self.model_cls.business_group==self.user.business_group]
        CRUDHandler.async_query_all_json(self, cond_list=cond_list, 
                                         order_list=order_list, 
                                         is_with_entity_id=is_with_entity_id, 
                                         cur_user=cur_user)    
    
class TeamHandler(CRUDHandler):
    @webapp2.cached_property
    def min_access_level(self):
        #user_role = UserRole.query(UserRole.role_name == config.TEAM_ADMIN.role_name).get()
        return config.TEAM_ADMIN.access_level
    
    @webapp2.cached_property
    def teams_in_group(self):
        if self.user.access_level == config.GROUP_ADMIN.access_level:
            teams_in_group = BusinessTeam.get_prop_id_list('team_name', 
                                                       cur_user=self.user)
        else:
            teams_in_group = None
        return teams_in_group    

    @webapp2.cached_property
    def business_group_id(self):
        return self.user.business_group.get().key.id()   
        
    @webapp2.cached_property
    def business_team_id(self):
        if self.user.business_team:
            return self.user.business_team.get().key.id()
        elif (self.user.access_level == config.GROUP_ADMIN.access_level):
            fake_team_id = self.request.cookies.get('fake_team_id')
            return fake_team_id  
            #print "fake_team_id" + self.request.cookies.get('fake_team_id')
        return None
    
    def set_default_country(self, form_data):
        field_list = form_data['field_list']
        for each in field_list:
            if each['prop_name'] == 'country':
                if self.user.business_team:
                    each['default_value'] = self.user.business_team.get().country
                elif self.user.fake_business_team:
                    each['default_value'] = self.user.fake_business_team.get().country
                else:
                    each['default_value'] = None
        return form_data

    def process_get_form_data(self, form_data):
        if self.teams_in_group:
            form_data['teams_in_group'] = self.teams_in_group
        form_data = super(TeamHandler, self).process_get_form_data(form_data)
        return form_data
    
    def get(self):
        if self.user.access_level == config.GROUP_ADMIN.access_level:
            fake_business_team = BusinessTeam.get_by_id(int(self.business_team_id)).key
            self.user.fake_business_team = fake_business_team
        CRUDHandler.get(self)   
                
    def post(self):
        self.request.POST['user_created'] = str(self.user.key.id())
        self.request.POST['business_group'] = str(self.business_group_id)
        self.request.POST['business_team'] = str(self.business_team_id)
        if self.user.access_level == config.GROUP_ADMIN.access_level:
            fake_business_team = BusinessTeam.get_by_id(int(self.business_team_id)).key
            self.user.fake_business_team = fake_business_team

        if (self.business_team_id==None and self.model_cls.unique_level == config.TEAM_UNIQUE.unique_level):
            #if not self.request.POST["formType"].startswith('async_query'):
            response = {}
            response['status'] = True
            response['message'] = "You need to be assigned to a team for the operation, please contact your group admin!"
            self.async_render_msg(response)
            logging.error(response['message'])
            return
        super(TeamHandler, self).post()
        
    def process_upload_data(self, upload_data):
        for each in upload_data:
            each['business_group'] = self.user.business_group
            if self.user.business_team:
                each['business_team'] = self.user.business_team
            elif hasattr(self.user, "fake_business_team"):
                each['business_team'] = self.user.fake_business_team
                
            each['user_created'] = self.user.key

        return upload_data

    
    def prepare_cond_list(self):
        cond_list = None
        if self.user.access_level <= config.TEAM_ADMIN.access_level and self.user.business_team:
            cond_list = [self.model_cls.business_group==self.user.business_group,
                     self.model_cls.business_team==self.user.business_team]
        elif self.user.access_level == config.GROUP_ADMIN.access_level and self.business_team_id:
            business_team = BusinessTeam.get_by_id(int(self.business_team_id)).key
            cond_list = [self.model_cls.business_group==self.user.business_group,
                     self.model_cls.business_team==business_team]
        return cond_list
        
        
    def async_query_all_json(self, 
                             cond_list=None, 
                             order_list=None, 
                             is_with_entity_id=True, 
                             cur_user=None):
        team_cond_list = self.prepare_cond_list()
        if cond_list != None:
            cond_list = team_cond_list + cond_list
        else:
            cond_list = team_cond_list
        CRUDHandler.async_query_all_json(self, 
                                         cond_list=cond_list, 
                                         order_list=order_list, 
                                         is_with_entity_id=is_with_entity_id, 
                                         cur_user=self.user)    

class TeamTemplateHandler(TeamHandler):
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
                del result['key']
                result['data'] = template_key.get().to_dict(cur_user=self.user) 
                return result 
        else:
            return None
    
    def process_upload_data(self, upload_data):
        upload_data = super(TeamTemplateHandler, self).process_upload_data(upload_data)
        if 'template_search_get_fields' in self.form:
            template_field_id = self.form['template_search_get_fields']
            for each in upload_data:
                each = self.set_template_value(template_field_id, each)
        return upload_data                 
