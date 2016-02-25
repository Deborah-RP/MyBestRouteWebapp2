import webapp2
import config
import logging

from handler.base import BaseHandler
from model import account
from utils.handler_utils import user_required
from google.appengine.api import users
import webapp2_extras.appengine.auth.models

class MainPage(BaseHandler):
    def get(self):
        '''
            Default index page
            based on various re-direct params
            set the cookie for front page to display error message
        '''
        
        login_flag = self.request.get('login')
        access_flag = self.request.get('access')
        verify_flag = self.request.get('verified')
        reset_flag = self.request.get('reset_pass')
        if login_flag:
            logging.info('login_required')
            self.response.set_cookie("login_required", "Yes")
            self.redirect("/")
        elif access_flag:
            logging.info('access_denied')
            self.response.set_cookie("access_denied", "Yes")
            self.redirect("/")
        elif verify_flag:
            logging.info('verified')
            self.response.set_cookie("verified", "Yes")
            self.redirect("/")
        elif reset_flag:
            logging.info('reset_pass')
            self.response.set_cookie("reset_pass", "Yes")
            self.redirect("/")            
        else:
            logging.info('None')
            self.render("index.html")
            
class HomePage(BaseHandler):
    def get(self):
        user = self.user
        last_logout_tm = user.last_logout_time
        self.homepage = {}
        self.get_sys_info(user, last_logout_tm)
        self.render('home.html', homepage=self.homepage)
    
        
    def get_sys_info(self, user, last_visit_tm):
        if user.access_level >= config.SYS_ADMIN.access_level:
            #Get all the user created since last logout
            cond_list = [account.User.tm_created > last_visit_tm]
            order_list = [account.User.tm_created]
            result = account.User.query_data_to_dict(cur_user=self.user,
                                                     cond_list=cond_list,
                                                     order_list=order_list)
            
            user_cnt = 0
            for each in result:
                if config.GROUP_ADMIN.access_level <= each['access_level'] <= user.access_level:
                    user_cnt += 1
                    
            self.homepage['new_user_num'] = user_cnt
            
            if user.role_name == config.SUPER_ADMIN.role_name:
                self.homepage['user_url'] = "/super_admin/users"
            else:
                self.homepage['user_url'] = "/sys_admin/users"
            
            cond_list = [account.PricePlan.tm_created > last_visit_tm]
            order_list = [account.PricePlan.tm_created]
            result = account.PricePlan.query_data_to_dict(cur_user=self.user,
                                                          cond_list=cond_list,
                                                          order_list=order_list)
            self.homepage['new_plan_num'] = len(result)
            self.homepage['priceplan_url'] = "/sys_admin/price_plan"
            
            cond_list = [account.BusinessGroup.status == config.PENDING_STATUS]
            result = account.BusinessGroup.query_data_to_dict(cur_user=self.user,
                                                              cond_list=cond_list,
                                                              order_list=order_list)
            
            self.homepage['new_group_num'] = len(result)
            self.homepage['group_url'] = "/sys_admin/activate_group"
            

class InitSystemHandler(BaseHandler):
    def get(self):
        admin_user = users.get_current_user()
        if admin_user:
            if users.is_current_user_admin():
                #print admin_user
                self.sys_init(admin_user)
                self.response.write('Performed System Initialization')
            else:
                #self.redirect(users.create_logout_url(self.request.uri))
                self.redirect(users.create_logout_url('/'))
        else:
            self.redirect(users.create_login_url(self.request.uri))
        
        
    def sys_init(self, admin_user):
        if account.PricePlan.query(account.PricePlan.plan_name == 'Basic Plan').get():
            return
        #create super user role 
        userrole_data = [
                         config.SUPER_ADMIN,
                         config.SYS_ADMIN,
                         config.GROUP_ADMIN,
                         config.TEAM_ADMIN,
                         config.TEAM_USER
                         ]

        super_admin_role = None
        for each in userrole_data:
            userrole = account.UserRole()
            userrole.populate(**each)
            userrole.put()
            if each['role_name'] == 'Super Admin':
                super_admin_role = userrole

        
       
        #create price plan
        priceplan_data = {
                     'plan_name': 'Basic Plan',
                     'plan_price': 0,
                     }
        
        priceplan = account.PricePlan()
        priceplan.populate(**priceplan_data)
        priceplan.put()
        
        #create business group
        bizgroup_data = {
                         'business_name': 'System Admin Group',
                         'price_plan': priceplan.key,
                         'status': 'Active',
                         'country': 'Singapore',
                         'timezone': '8',
                         }
        
        bizgroup = account.BusinessGroup()
        bizgroup.populate(**bizgroup_data)
        bizgroup.put()

        userrole = account.UserRole.query(account.UserRole.role_name=='Super Admin').get()
        print userrole
        
        user_data = {
                     'email': admin_user.email(),
                     'user_name': 'GAE Admin',
                     'password_raw': '12345678',
                     'user_role': super_admin_role.key,
                     'business_group': bizgroup.key,
                     'status': 'Active',
                     'verified': True
                     }        
        #result = account.User.create_model_entity(user_data)
        result = webapp2_extras.appengine.auth.models.User.create_user(user_data['email'], 
                                                              None,
                                                              **user_data)
        logging.info(result)

class UserChannelHandler(BaseHandler):
    @user_required
    def post(self):
        channel = account.UserChannel.create_user_channel(self.user.email_lower)
        channel = channel.to_dict(cur_user=self.user)
        self.render_json(channel)
        
class UploadRoute(BaseHandler):
    def get(self):
        self.render("upload_route.html")

class AnalyzeRoute(BaseHandler):
    def get(self):
        self.render("analyze_route.html")

app = webapp2.WSGIApplication([
    (r'/$', MainPage),
    (r'/home$', HomePage),
    (r'/init_sys$', InitSystemHandler),
    (r'/user_channel$', UserChannelHandler),
    (r'/upload_route$', UploadRoute),
    (r'/analyze_route$', AnalyzeRoute),	
], config=config.WSGI_CONFIG, debug=config.DEBUG)