import json
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch


from handler.base import BaseHandler
from model.account import UserRole
from model.base_doc import SGPostal



class DocumentHandler(BaseHandler):
    @user_required
    def __init__(self, *arg, **kwargs):
        super(DocumentHandler, self).__init__(*arg, **kwargs)
        
    @webapp2.cached_property
    def min_access_level(self):
        user_role = UserRole.query(UserRole.role_name == config.SUPER_ADMIN).get()
        return user_role.access_level
    

class UpdatePostalSearch(DocumentHandler):
    def get(self):
        #Delete all the old items in the index
        SGPostal.delete_all_in_index()
    
        #10 json files contains the address info
        for i in range(1):
            jsonUrl = "https://s3-ap-southeast-1.amazonaws.com/clt-friso/%dpostal.json" % i
            logging.debug("Downloading json file %d" %i)
            urlfetch.set_default_fetch_deadline(40)
            result = urlfetch.fetch(jsonUrl)
            if result.status_code == 200:
                #logging.debug("Download complete")
                #logging.debug("Loading json file")
                
                myData = json.loads(result.content)    
                logging.debug("File loaded, total %d items" % len(myData))
                chunks=[myData[x:x+250] for x in xrange(0, len(myData), 250)]
                i = 1
                for chunk in chunks:
                    logging.debug(str(len(chunk)))
                    strChunk = json.dumps(chunk)
                    taskqueue.add(url='/super_admin/parse_postal', countdown = 60, params = {'postalRows': strChunk, "item": i, "total": len(chunks), 'total_items': len(myData)}, queue_name='updatepostal')
                    i += 1
            else:
                logging.debug("File %d not found" % i)                    

class ParsePostalHandler(DocumentHandler):
    def post(self):
        stringData = self.request.get("postalRows")
        myData = json.loads(stringData)
        
        item = self.request.get("item")
        total = self.request.get("total")
        total_items = self.request.get("total_items")
        
        logging.debug(str(item) + "/" + str(total))
        SGPostal.build_doc_batch(mydata)
                         

app = webapp2.WSGIApplication([
    (r'/super_admin/update_postal$', UpdatePostalSearch),
    (r'/super_admin/parse_postal$', ConfigFormHandler),
], config=config.WSGI_CONFIG, debug=config.DEBUG)    
