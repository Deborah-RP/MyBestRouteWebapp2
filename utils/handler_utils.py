from google.appengine.api import mail 

def construct_return_msg(success_cnt, fail_cnt, operation, 
                         success_message, fail_message):
    msg = ""
    status = True
    if success_cnt >= 1:
        if fail_cnt == 0:
            msg = "%s (%s records)" %(success_message, success_cnt)
        else:
            msg = "%s %s records successfully! " %(operation, success_cnt)
        
    if fail_cnt > 0:
        msg += "%s records fail, %s" %(fail_cnt, fail_message)
    
    if success_cnt == 0 and fail_cnt == 0:
        msg = "No data to %s" %(operation)
        status = False
    
    result = {}
    result['status'] = status
    result['message'] = msg
    return result

def user_required(handler):
    """
    Decorator that checks if there's a user associated with the current session.
    Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        user = self.user
        if not user:
            self.redirect("/?login=1", abort=True)
        else: 
            if user.access_level < self.min_access_level or user.access_level > self.max_access_level:
                self.redirect("/?access=1", abort=True)
            else:
                return handler(self, *args, **kwargs)
    return check_login
          
def send_email(to_address, subject, msg):
    sender = "deborah.coiscm@gmail.com"
    mail.send_mail(sender, to_address, subject, msg)
    
def send_verfication_email(user_name, user_email, verification_url):
    subject = "Your account has been approved"
    msg = ("""
    Dear %s:
    
    Your account has been approved. Please click at %s to verify your email address.

""" %(user_name, verification_url))
    send_email(user_email, subject, msg)
    
def send_reset_passwd_email(user_name, user_email, verification_url):
    subject = "Reset Password"    
    msg = ("""
    Dear %s:
    
    Please click at %s to reset your password.

""" %(user_name, verification_url))
    send_email(user_email, subject, msg)
    

    