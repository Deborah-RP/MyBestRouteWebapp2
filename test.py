import webapp2
import config
import json
from handler import base

class TestJinja2(base.BaseHandler):
    def get(self):
        self.render("test_jinja2.html")
        
class TestEditor(base.BaseHandler):
    def get(self):
        self.render("test_editor.html")
        
class TestEditorRead(base.BaseHandler):
    def get(self):
        data = {}
        data['data'] = [
        {
      "DT_RowId": "row_1",
      "first_name": "Tiger",
      "last_name": "Nixon",
      "position": "System Architect",
      "email": "t.nixon@datatables.net",
      "office": "Edinburgh",
      "extn": "5421",
      "age": "61",
      "salary": "320800",
      "start_date": "2011-04-25"
    },
    {
      "DT_RowId": "row_2",
      "first_name": "Garrett",
      "last_name": "Winters",
      "position": "Accountant",
      "email": "g.winters@datatables.net",
      "office": "Tokyo",
      "extn": "8422",
      "age": "63",
      "salary": "170750",
      "start_date": "2011-07-25"
    },
    ]
        self.render_json(data)                    
        
app = webapp2.WSGIApplication([
    (r'/test/test_jinja2$', TestJinja2),
    (r'/test/test_editor$', TestEditor),
    (r'/test/test_editor_read$', TestEditorRead),
    
], config=config.WSGI_CONFIG, debug=config.DEBUG)