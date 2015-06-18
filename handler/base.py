"""
Define the various classes for RequestHandler
"""

import webapp2
import config
import json

from config import JINJA_ENV

#from utils import ga_tracking

from webapp2_extras import sessions

"""
Base class for all the handlers used in the system
"""
class BaseHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        #Set self.request, self.response and self.app
        self.initialize(request, response)
                        
        #Add google analytics tracking.
        #ga_tracking.track_event_to_ga(request.path, "Get", "View", "100")
    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        #Key for OneMap API Javascript
        params['onemap_key'] = config.ONEMAP_KEY
        t = JINJA_ENV.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)
    
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)       # dispatch the main handler
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)
            
    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()
