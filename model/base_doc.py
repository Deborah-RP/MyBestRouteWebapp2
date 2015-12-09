import logging
import string
import config
from utils.map_utils import Geocode_API 
from config import DEBUG
from google.appengine.api import search
'''
    Abstract class. 
    Provide helper methods to manage search.Documents
'''
class BaseDocument(object):
    _INDEX_NAME = None
    _VISIBLE_PRINTABLE_ASCII = frozenset(
    set(string.printable) - set(string.whitespace))
    
    @classmethod
    def is_valid_doc_id(cls, doc_id):
        for char in doc_id:
            if char not in __VISIBLE_PRINTABLE_ASCII:
                return False
        return not doc_id.startswith('!')
    
    @classmethod
    def get_index(cls):
        return search.Index(name=cls._INDEX_NAME)

    @classmethod
    def delete_all_in_index(cls):
        doc_index = cls.get_index()
        try:
            while True:
            # until no more documents, get a list of documents,
            # constraining the returned objects to contain only the doc ids,
            # extract the doc ids, and delete the docs.
                document_ids = [document.doc_id for document in doc_index.get_range(ids_only=True)]
                if not document_ids:
                    break
                doc_index.delete(document_ids)
        except search.Error:
            logging.exception("Error removing documents:")
        
    @classmethod
    def add_docs(cls, docs):
        """wrapper for search index add method; specifies the index name."""
        try:
            return cls.get_index().put(docs)
        except search.Error:
            logging.exception("Error adding documents.")

    '''
        Build the documents in batch, based on the given 
        list of records. This is used for creating new documents. 
    '''
    @classmethod
    def build_doc_batch(cls, records):
        docs = []
        for record in records:
            #try:
                new_doc = cls.create_doc(record)
                docs.append(new_doc)
            #except:
                #logging.error('error creating document from data: %s', record)
                
        try:
            logging.info('records:%s, docs:%s' %(len(records), len(docs)))
            add_results = cls.add_docs(docs)
        except search.Error:
            logging.exception('Add failed')
        return
    
    '''
        Return the document with the given doc id.
        If the doc_id is not in the index, return None
    '''
    @classmethod
    def get_doc_by_id(cls, doc_id):
        index = cls.get_index()
        return index.get(doc_id)
    
    @classmethod
    def query_doc(cls, query_string):
        index = cls.get_index()
        results = index.search(query_string)
        print (results)
        return results
    
    @classmethod
    def doc_to_dict(cls, doc):
        doc_dict = {}
        for field in doc.fields:
            doc_dict[field.name] = field.value
            
            if isinstance(field.value, search.GeoPoint):
                doc_dict[field.name] = "%s, %s" %(field.value.latitude, field.value.longitude)
        return doc_dict
            
    @classmethod
    def get_record_dict(cls, doc_id=None, query_string=None):
        result_rec = None
        if doc_id:
            doc_rec = cls.get_doc_by_id(doc_id)
        elif query_string:
            doc_rec = cls.query_doc(query_string)
            
            if doc_rec.results:
                if len(doc_rec.results) == 0:
                    result_rec = None
                else:
                    result_rec = []
                    for each in doc_rec.results:
                        each = cls.doc_to_dict(each)
                        result_rec.append(each)
            else:
                result_rec = None
        
        return result_rec    
'''
    Document class for Singapore postal address.
    The postal code of an address will be used as the doc_id.
    This will allow the record to be reindex given the info,
    without having to fetch the existing document
'''

class AddressDocument(BaseDocument):
    _INDEX_NAME = config.ADDRESS_INDEX_NAME
    
    @staticmethod
    def create_address_dict(record):
        address = {}
        address['country'] = record.get('country')
        address['postal'] = record.get('postal')
        address['building'] = record.get('building')
        address['street'] = record.get('street')
        address['city'] = record.get('city')
        address['state'] = record.get('state')
        address['formatted_address'] = record.get('formatted_address')
        
        return address
    
    @staticmethod
    def create_address_fields(address):
        address_fields = [
                  search.TextField(name='country', value=address['country']),
                  search.TextField(name='postal', value=address['postal']), 
                  search.GeoField(name='latlng',value=address['geopoint']),
                  search.TextField(name='building', value=address['building']), 
                  search.TextField(name='street', value=address['street']),
                  search.TextField(name='city', value=address['city']),
                  search.TextField(name='state',value=address['state']),
                  search.TextField(name='formatted_address',value=address['formatted_address'])
                  ]
        
        return address_fields        
            
    @classmethod
    def add_doc_from_geocode_api(cls, address):
        address = Geocode_API.get_geocode_by_address(address)
        
        if address == None:
            return address
        
        if 'lat' in address and 'lng' in address:
            address['geopoint'] = search.GeoPoint(address.get('lat'), address.get('lng'))
            if 'doc_id' in address:
                doc_id = address['doc_id']
                address_fields = cls.create_address_fields(address)
                new_doc = search.Document(doc_id=doc_id, fields=address_fields)
                index = cls.get_index()
                index.put(new_doc)
                address = new_doc
            else:
                address = None
        else:
            address = None
        return address
        
    @classmethod
    def get_address_doc_record(cls, doc_rec):
        doc_id = None
        query_string = ""
        
        address = cls.create_address_dict(doc_rec)
        print (address)
        for key, value in address.items():
            if key == "formatted_address":
                continue
            
            if value and len(value) > 0:
                sub_query = "%s:%s" %(key,value)
                if len(query_string) > 0:
                    query_string += " AND %s" %sub_query
                else:
                    query_string = sub_query
        
        if DEBUG:
            logging.info("query_string:%s" %(query_string))
            
        record = cls.get_record_dict(doc_id=None, query_string=query_string)
        
        #record not found in search index, get the geocode from api
        if not record:
            record = cls.add_doc_from_geocode_api(address)
            if record: 
                record = [cls.doc_to_dict(record)]
        return record

class SGAdressDocument(AddressDocument):
    @classmethod
    def create_address_dict(cls, record):
        address = {}
        address['country'] = "Singapore"
        address['postal'] = record.get('postal')
        address['building'] = record.get('building')
        if address['building'] == None or address['building'] == "":
            address['building'] = record.get('block')
        address['street'] = record.get('street')
        address['city'] = ""
        address['state'] = ""
        address['formatted_address'] = "%s %s, %s %s" %(address['building'],
                                                        address['street'],
                                                        address['country'],
                                                        address['postal'])
        address['doc_id'] = "Singapore+"+address['postal']
        return address
    
    #Only used first system initialization
    @classmethod
    def create_doc(cls, record):
        address = cls.create_address_dict(record)
        if 'lat' in record and 'lng' in record:
            geopoint = search.GeoPoint(record.get('lat'), record.get('lng'))
        else:
            address = Geocode_API.get_geocode_by_address(address)
            if 'lat' in address and 'lng' in address:
                geopoint = search.GeoPoint(address['lat'], address['lng'])
            else:
                geopoint = search.GeoPoint(float(0), float(0))
       
        fields = [
                  search.TextField(name='country', value=address['country']),
                  search.TextField(name='postal', value=address['postal']), 
                  search.GeoField(name='latlng',value=geopoint),
                  search.TextField(name='building', value=address['building']), 
                  search.TextField(name='street', value=address['street']),
                  search.TextField(name='city', value=address['city']),
                  search.TextField(name='state',value=address['state']),
                  search.TextField(name='formatted_address',value=address['formatted_address'])                  
                  ]
        
        if 'doc_id' in address:
            doc_id = address['doc_id']
        else:
            doc_id = None
        new_doc = search.Document(doc_id=doc_id, fields=fields)
        return new_doc    