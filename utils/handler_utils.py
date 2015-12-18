import os
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

    
def get_current_location():
    city = os.environ.get('HTTP_X_APPENGINE_CITY', 'Unknown City').capitalize()
    country = os.environ.get('HTTP_X_APPENGINE_COUNTRY', 'Unknown Country')
    return "%s, %s" %(city, country)
    
    