import webapp2
import config
import logging
import time

from datetime import datetime

from handler.base import BaseHandler
from model.account import User
from utils.ndb_utils import *
from utils.handler_utils import *
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError


class AuthHandler(BaseHandler):
    def create_new_user(self, v_type):
        if self.user:
            self.request.POST['user_access_level'] = self.user.access_level
        else:
            self.request.POST['user_access_level'] = 1
        status, user_data = self.model_cls.create_model_entity(self.request.POST)
        if status:
            user = user_data[1]
            user_id = user.get_id()
            token = self.user_model.create_signup_token(user_id)
            verification_url = self.uri_for('user_verification', type=v_type, user_id=user_id, signup_token=token, _full=True)
            send_verfication_email(user.user_name, user.email, verification_url)
            if DEBUG:
                logging.info("verification_url : %s" %verification_url)
            
            if v_type == 'vp':
                msg = "A verification email has been sent to user email account!"
            elif v_type == 'v':
                msg = 'A verification email has been sent to the your account!'
        else:
            msg = user_data
        return status, msg            

class LoginHandler(BaseHandler):
    def post(self):
        email_lower = self.request.get('email').lower()
        password = self.request.get('password')
        try:
            user = self.auth.get_user_by_password(email_lower, password, remember=True, save_session=True)
            if (not self.user.verified):
                self.auth.unset_session()
                self.async_render_msg(False, "Please verify your email address first!")
                return
                
            if (self.user.status != 'Active'):
                self.auth.unset_session()
                self.async_render_msg(False, "This account is not active, please contact system administrator!")
                return
            
            self.user.failed_login_count = 0
            self.user.last_login_time = datetime.now()
            self.user.last_host_address = self.request.remote_addr
            self.user.put()
            self.async_render_msg(True, "Login successfully!", "/home")
        except (InvalidAuthIdError, InvalidPasswordError) as e:
            logging.info('Login failed for %s because of %s', email_lower, type(e))
            msg = "Login failed due to invalid email or password!"
            
            user = self.user_model.get_by_auth_id(email_lower)
            
            user.last_failed_login = datetime.now()
            user.failed_login_count +=1
            user.last_host_address = self.request.remote_addr
            if user.failed_login_count > 20:
                user.status = 'Failed Login Locked'
                msg = "Account is locked due to too many failed login attempts!"
            user.put() 
            delay = user.failed_login_count/3
            time.sleep(delay)
            self.async_render_msg(False, msg)
            
class LogoutHandler(BaseHandler):
    def get(self):
        self.auth.unset_session()
        self.redirect('/')
        
class ForgotPasswordHandler(BaseHandler):
    def post(self):
        email_lower = self.request.get('email').lower()
        user = self.user_model.get_by_auth_id(email_lower)
        status = True
        if not user:
            logging.info('Could not find any user entry for %s', email_lower)
            self.async_render_msg(status, "Invalid email address.")
            return
        
        if (user.status != 'Active'):
            self.async_render_msg(False, "This account is not active, please contact system administrator!")
            return
            
        user_id = user.get_id()
        token = self.user_model.create_signup_token(user_id)
        verification_url = self.uri_for('user_verification', type='p', user_id=user_id,
                                        signup_token=token, _full=True)
        if DEBUG:
            logging.info("Forgot password verification_url : %s" %verification_url)
        send_reset_passwd_email(user.user_name, user.email, verification_url)    
        msg = 'An email to reset password has been sent to your account.'
        self.async_render_msg(status, msg)
        
   
class SignupHandler(AuthHandler):
    def __init__(self, *arg, **kwargs):
        super(SignupHandler, self).__init__(*arg, **kwargs)
        self.model_cls = User
        
    def post(self):
        status, msg = self.create_new_user("v")
        self.async_render_msg(status, msg)
        
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
        
        if verfication_type == 'vp':
            user.verified = True
            user.status = 'Active'
            
        user.put()
        self.user_model.delete_signup_token(user.get_id(), old_token)
        self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
        self.redirect("/?verified=1")
        
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
        
        if verification_type == 'v':
            # remove signup token, we don't want users to come back with an old link
                    # store user data in the session
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            self.user_model.delete_signup_token(user.get_id(), signup_token)
            if not user.verified:
                user.verified = True
                user.status = 'Active'
                user.put()
            self.redirect("/?verified=1")
            return
        elif verification_type == 'p' or verification_type == 'vp':
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