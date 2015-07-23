import webapp2
import config

from handler.base import BaseHandler

class MainPage(BaseHandler):
    def get(self):
        login_flag = self.request.get('login')
        access_flag = self.request.get('access')
        verify_flag = self.request.get('verified')
        if login_flag:
            self.response.set_cookie("login_required", "Yes")
            self.redirect("/")
        elif access_flag:
            self.response.set_cookie("access_denied", "Yes")
            self.redirect("/")
        elif verify_flag:
            self.response.set_cookie("verified", "Yes")
            self.redirect("/")
        else:
            self.render("index.html")
            
class HomePage(BaseHandler):
    def get(self):
        self.render('home.html')
        
class UploadRoute(BaseHandler):
    def get(self):
        self.render("upload_route.html")

class AnalyzeRoute(BaseHandler):
    def get(self):
        self.render("analyze_route.html")

app = webapp2.WSGIApplication([
    (r'/$', MainPage),
    (r'/home$', HomePage),
    (r'/upload_route$', UploadRoute),
    (r'/analyze_route$', AnalyzeRoute),
		
], config=config.WSGI_CONFIG, debug=config.DEBUG)