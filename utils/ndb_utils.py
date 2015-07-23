import logging
import webapp2

from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata

from config import DEBUG

def get_kind_by_name(kind_name):
    kind_map = ndb.Model._kind_map
    model_cls = kind_map[kind_name]
    return model_cls 

def get_all_kind_names():
    all_kind = metadata.get_kinds()
      
    if DEBUG:
        logging.info(all_kind)
    return all_kind.sort()

#Return kind name and property name or KeyProperty
def get_key_prop_val(key_prop):
    model_cls = get_kind_by_name(key_prop._kind)
    v_name = key_prop._verbose_name
    return model_cls, v_name

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False