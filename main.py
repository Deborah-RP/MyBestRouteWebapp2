import webapp2
import config
from handler import base

class MainPage(base.BaseHandler):
    def get(self):
        self.render("index.html")
        
class UploadRoute(base.BaseHandler):
    def get(self):
        self.render("upload_route.html")

class AnalyzeRoute(base.BaseHandler):
    def get(self):
        self.render("analyze_route.html")
		
class TestJinja2(base.BaseHandler):
    def get(self):
        self.render("test_jinja2.html")
        
app = webapp2.WSGIApplication([
    (r'/', MainPage),
    (r'/upload_route$', UploadRoute),
    (r'/analyze_route$', AnalyzeRoute),
	(r'/test_jinja2$', TestJinja2),
	
], config=config.WSGI_CONFIG, debug=config.DEBUG)