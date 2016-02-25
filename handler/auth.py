import webapp2
import config
import logging
import time, datetime

from handler.base import BaseHandler
from model.account import *
from utils.handler_utils import *
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError


class AuthHandler(BaseHandler):
    def send_verfication_email(self, user_name, user_email, verification_url):
        subject = "Your account has been approved"
        msg = ("""
        Dear %s:
        
        Your account has been approved. 
        
        You can now visit %s to verify your account and sign in to access the website.
        
        The Route Planner Team
    
    """ %(user_name, verification_url))
        self.send_email(user_email, subject, msg)
    
    def create_new_user(self, v_type):
        response = {}
        
        #Get current user access level
        if self.user:
            self.request.POST['user_access_level'] = self.user.access_level
        else:
            self.request.POST['user_access_level'] = UserRole.query(
                UserRole.role_name == config.DEFAULT_USER_ROLE.role_name).get().access_level
        
        #Create a new user
        response = self.model_cls.create_model_entity(model_rec=self.request.POST)
        
        if response['status'] == True:
            user = response['user_data'][1]
            user_id = user.get_id()
            
            #Create auth token
            token = self.user_model.create_signup_token(user_id)
            
            #Create verification uri
            verification_url = self.uri_for('user_verification', type=v_type, user_id=user_id, signup_token=token, _full=True)
            
            #Send verification email
            self.send_verfication_email(user.user_name, user.email, verification_url)
            
            logging.info("verification_url for %s : %s" %(user.user_name, verification_url))
            
            #vp is user created by admin, v is a new user sighup
            if v_type == config.NEW_USER_VERIFICATION:
                msg = "A verification email has been sent to user email account!"
                
            elif v_type == config.SIGNUP_VERIFICATION:
                msg = 'A verification email has been sent to the your account!'
            
            response['message'] = msg
            response['entity'] = user 
        return response            

class LoginHandler(BaseHandler):
    def post(self):
        email_lower = self.request.get('email').lower()
        password = self.request.get('password')
        response = {}
        try:
            user = self.auth.get_user_by_password(email_lower, password, remember=False, save_session=True)
            if (not self.user.verified):
                self.auth.unset_session()
                response['status'] = False
                response['message'] = "Please verify your email address first!"
                self.async_render_msg(response)
                return
            
            if (self.user.group_status != config.ACTIVE_STATUS):
                self.auth.unset_session()
                response['status'] = False
                response['message'] = "The business group account is not active, please contact system administrator!"
                self.async_render_msg(response)
                return
                
            if (self.user.status != config.ACTIVE_STATUS):
                self.auth.unset_session()
                response['status'] = False
                response['message'] = "This account is not active, please contact system administrator!"
                self.async_render_msg(response)
                return
            
            self.user.failed_login_count = 0
            self.user.last_login_time = datetime.datetime.now()
            self.user.last_host_address = self.request.remote_addr
            self.user.put()
            response['status'] = True
            response['message'] = "Login successfully!"
            self.async_render_msg(response, config.USER_HOME_PAGE)            
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            logging.info('Login failed for %s because of %s', email_lower, type(e))
            
            response['status'] = False
            response['message'] = "Login failed due to invalid email or password!"
            
            user = self.user_model.get_by_auth_id(email_lower)
            if user:
                
                user.last_failed_login = datetime.datetime.now()
                user.failed_login_count += 1
                user.last_host_address = self.request.remote_addr
                
                if user.failed_login_count > 20:
                    user.status = config.FAILED_LOGIN_LOCKED_STATUS
                    response['message'] = "Account is locked due to too many failed login attempts!"
                    delay = user.failed_login_count/3
                    time.sleep(delay)
                user.put()    
            self.async_render_msg(response)
            
class LogoutHandler(BaseHandler):
    def get(self):
        self.user.last_logout_time = datetime.datetime.now()
        self.user.put()
        self.auth.unset_session()
        self.redirect('/')
        
class ForgotPasswordHandler(BaseHandler):
    def send_reset_passwd_email(self, user_name, user_email, verification_url):
        subject = "Reset Password"    
        msg = ("""
        Dear %s:
        
        Please click at %s to reset your password.
    
    """ %(user_name, verification_url))
        self.send_email(user_email, subject, msg)    
    
    def post(self):
        email_lower = self.request.get('email').lower()
        user = self.user_model.get_by_auth_id(email_lower)
        response = {}

        if not user:
            logging.info('Could not find any user entry for %s', email_lower)
            response['status'] = False
            response['message'] = "Invalid email address."
            #self.async_render_msg(status, "Invalid email address.")
            self.async_render_msg(response)
            return
        
        if (user.status != config.ACTIVE_STATUS):
            print user
            response['status'] = False
            response['message'] = "This account is not active, please contact system administrator!"            
            self.async_render_msg(response)
            return
            
        user_id = user.get_id()
        token = self.user_model.create_signup_token(user_id)
        verification_url = self.uri_for('user_verification', type=config.FORGOT_PASSWORD_VERIFICATION, 
                                        user_id=user_id, signup_token=token, _full=True)
        if DEBUG:
            logging.info("Forgot password verification_url : %s" %verification_url)
        self.send_reset_passwd_email(user.user_name, user.email, verification_url)
        response['status'] = True    
        response['message'] = 'An email to reset password has been sent to your account.'
        self.async_render_msg(response)
        
   
class SignupHandler(AuthHandler):
    def __init__(self, *arg, **kwargs):
        super(SignupHandler, self).__init__(*arg, **kwargs)
        self.model_cls = User
        
    def post(self):
        
        #Each new user will create a new business gorup
        #Default plan for new user
        price_plan = PricePlan.query(
                    PricePlan.plan_name == config.DEFAULT_PRICE_PLAN).get()
        if not price_plan:
            response = {}
            response['status'] = False
            response['message'] = 'No default price plan, please contact system admin!'
            self.async_render_msg(response)
            return 
        
        self.request.POST['price_plan'] = str(price_plan.key.id())
        response = BusinessGroup.create_model_entity(model_rec=self.request.POST)
        if response['status'] != True:
            self.async_render_msg(response)
            return 
        else:
            business_group = response['entity'].key
            self.request.POST['business_group'] = business_group.id()
        
        #Default sign up user role is "Group Admin"
        user_role = UserRole.query(UserRole.role_name == config.DEFAULT_USER_ROLE.role_name).get()
        if not user_role:
            response = {}
            response['status'] = False
            response['message'] = 'No default user role, please contact system admin!'
            business_group.delete()
            self.async_render_msg(response)
            return 
        
        self.request.POST['user_role'] = str(user_role.key.id())        
        response = self.create_new_user(config.SIGNUP_VERIFICATION)
        if response['status'] != True:
            #Delete the business group if user cannot be created
            business_group.delete()
        
        self.async_render_msg(response)
        
class ResetPasswordHandler(BaseHandler):
    def post(self):
        password = self.request.get('password')
        if not password or password != self.request.get('confirm_password'):
            self.render("reset_password.html", msg="Password does not match!")
            return
        
        user_id = self.request.get('u')
        old_token = self.request.get('t')
        verfication_type = self.request.get('vt')
        user, ts = self.user_model.get_by_auth_token(int(user_id), old_token, 'signup')
        
        if not user:
            logging.info('Could not find any user with id "%s" token "%s"',user_id, old_token)
            self.render("reset_password.html", msg="Invalid token!")  
            return
        
        user.set_password(password)
        
        if verfication_type == config.NEW_USER_VERIFICATION:
            user.verified = True
            user.status = config.ACTIVE_STATUS
            
        user.put()
        self.user_model.delete_signup_token(user.get_id(), old_token)
        if user.group_status != config.ACTIVE_STATUS:
            self.auth.unset_session()
        else: 
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            #self.redirect("/?verified=1")
        self.redirect("/?reset_pass=1")
        
class VerificationHandler(BaseHandler):
    def get(self, *args, **kwargs):
        user = None
        user_id = kwargs['user_id']
        signup_token = kwargs['signup_token']
        verification_type = kwargs['type']
        user, ts = self.user_model.get_by_auth_token(int(user_id), signup_token, 'signup')
        if not user:
            logging.info('Could not find any user with id "%s" signup token "%s"', user_id, signup_token)
            self.abort(404)
        
        if verification_type == config.SIGNUP_VERIFICATION:
            # remove signup token, we don't want users to come back with an old link
            # store user data in the session
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            self.user_model.delete_signup_token(user.get_id(), signup_token)
            if not user.verified:
                user.verified = True
                user.status = config.ACTIVE_STATUS
                user.put()
            
            if user.group_status != config.ACTIVE_STATUS:
                self.auth.unset_session()
                self.redirect('/')
            else:
                self.redirect("/?verified=1")
            return
        elif verification_type == config.FORGOT_PASSWORD_VERIFICATION \
                                or verification_type == config.NEW_USER_VERIFICATION:
            params = {
                'user_id': user_id,
                'token': signup_token,
                'verification_type': verification_type,
            }
            self.render('reset_password.html', **params)
        else:
            logging.info('verification type not supported')
            self.abort(404)
    
verfication_route = webapp2.Route('/auth/verfication/<type:v|p|vp>/<user_id:\d+>-<signup_token:.+>',
      handler=VerificationHandler, name='user_verification')
         
app = webapp2.WSGIApplication([
    (r'/auth/login$', LoginHandler),
    (r'/auth/logout$', LogoutHandler),
    (r'/auth/signup$', SignupHandler),
    (r'/auth/forgotpasswd$', ForgotPasswordHandler),
    (r'/auth/reset_password$', ResetPasswordHandler),
    verfication_route,
], config=config.WSGI_CONFIG, debug=config.DEBUG)