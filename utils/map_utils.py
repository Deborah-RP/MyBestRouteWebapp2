import json
import logging
import datetime
import config
import urllib
import string

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

from config import DEBUG

class OneMapToken(ndb.Model):
    token = ndb.StringProperty(required=True)
    expired = ndb.DateTimeProperty(required=True)
    
    @classmethod
    def query_token(cls):
        return cls.query().get()
    '''
        Function to get the onemap token for REST API.
        The token is a short lived one (24 hrs) based on the AccessKEY.
        The JSON response from url is
        {"GetToken":[{"NewToken":"3UE9oKyubVzDh/mXFqqsGOtdBgCjdIB17nd99i7yLWVn3XSP+DVcrkuX"}]}
    '''        
    @classmethod
    def get_onemap_token(cls):
        #If the token still available (< 24 hours)
        token = cls.query_token() 
        if token:
            if token.expired > datetime.datetime.now():
                if DEBUG:
                    logging.info('Onemap token from datastore')
                return token.token
            else:
                token.key.delete()
        
        #Get a new token and save it into session
        onemap_token_url = 'http://www.onemap.sg/API/services.svc/getToken?accessKEY=%s' %config.ONEMAP_KEY
        logging.info("The onemap token url is %s" %onemap_token_url)
    
        response = urlfetch.fetch(onemap_token_url)
        if response.status_code == 200:
            token = OneMapToken()
            response_data = json.loads(response.content)
            token.token = response_data['GetToken'][0]['NewToken']
            token.expired = datetime.datetime.now() + datetime.timedelta(hours=24)
            token.put()
            if DEBUG:
                logging.info('onemap_token : %s' %token)
            return token.token
        else:
            logging.info("Cannot retrieve onemap token %s" %response)
            return None


class Geocode_API:
    '''
    function to retreive geocode from service provider
    '''
    @classmethod  
    def get_geocode_by_address(cls, address):
        if address['country'] == "Singapore":
            api_provider = "onemap"
            #api_provider = "google"
        else:
            api_provider = "google"
        address = cls.search_geocode(address, api_provider)
        return address
    
    @staticmethod
    def _onemap_address_informat(address):
        if address['postal'] != None and address['postal'] != "":
            valid_address = address['postal']
        else:
            valid_address = "%s, %s" %(address['building'], address['street'])
        return urllib.quote_plus(valid_address)
    
    @staticmethod
    def _google_address_informat(address):
        address_name = ['building', 'street', 'city', 'state', 'postal', 'country']
        valid_address = ""
        for each in address_name:
            if (address[each] and address[each] != ""):
                if (len(valid_address) > 0):
                    valid_address += "+"+address[each]
                else:
                    valid_address = address[each]
        return urllib.quote_plus(valid_address)        
    
    @staticmethod
    def _mapquest_address_informat(address):
        valid_address = {}
        tmp_address = {}
        if address['building'] != "":
            tmp_address['street'] = "%s %s" %(address['building'], address['street'])
        else:
            tmp_address['street'] = address['street']
        tmp_address['city'] = address['city']
        tmp_address['state'] = address['state']
        tmp_address['postal'] = address['postal']
        tmp_address['country'] = address['country']
        valid_address['location'] = tmp_address
        return urllib.quote(json.dumps(valid_address))
    
    @classmethod
    def get_geocode_api_informat(cls, address, api_provider):
        if (api_provider == 'onemap'):
            valid_address = cls._onemap_address_informat(address)
        elif (api_provider == 'google'):
            valid_address = cls._google_address_informat(address)
        elif (api_provider == 'mapquest'):
            valid_address = cls._mapquest_address_informat(address)
        return valid_address
        
    @staticmethod
    def _onemap_geo_url(valid_address):
        onemap_token = OneMapToken.get_onemap_token()
        onemap_geo_url = ("http://www.onemap.sg/APIV2/services.svc/"
                          "basicSearchV2?token=%s&searchVal=%s"
                          "&otptFlds=SEARCHVAL,CATEGORY"
                          "&returnGeom=1&rset=1&projSys=WGS84"
                          ) %(onemap_token, valid_address)
                          
        return onemap_geo_url
    
    @staticmethod
    def _google_geo_url(valid_address):
        google_key = config.GOOGLE_KEY
        google_geo_url = ("https://maps.googleapis.com/maps/api/"
                          "geocode/json?address=%s&key=%s"
                          ) %(valid_address, google_key)
        return google_geo_url
    
    @staticmethod
    def _mapquest_geo_url(valid_address):
        mapquest_key = config.MAPQUEST_KEY
        mapquest_geo_url = ("http://www.mapquestapi.com/geocoding/v1/"
                            "address?key=%s&inFormat=json&"
                            "json=%s"
                            ) %(mapquest_key, valid_address)
        return mapquest_geo_url
    
    @classmethod
    def get_geo_url(cls, valid_address, api_provider):
        if api_provider == "onemap":
            geo_url = cls._onemap_geo_url(valid_address)
        elif api_provider == "google":
            geo_url = cls._google_geo_url(valid_address)
        elif api_provider == "mapquest":
            geo_url = cls._mapquest_geo_url(valid_address)
        return geo_url

    '''
    Example of return JSON:
    {"SearchResults":[{"PageCount":"0"},
    {"SEARCHVAL":"738964","CATEGORY":"Building","X":"103.7844","Y":"1.4438"}]}
    '''
    
    @staticmethod
    def _onemap_gecode_address_outformat(response_data, address):
        response_data = json.loads(response_data)
        if len(response_data['SearchResults']) >= 2:
            search_result = response_data['SearchResults'][1]
            '''
            geopoint = {}
            geopoint['lat'] = float(search_result['Y'])
            geopoint['lng'] = float(search_result['X'])
            '''
            address['lat'] = float(search_result['Y'])
            address['lng'] = float(search_result['X'])
            if address['postal'] != "":
                address['doc_id'] = "Singapore+"+address['postal']
        return address
    
    @staticmethod
    def parse_google_address_components(address_list, address):
        for each in address_list:
            if 'street_number' in each['types']:
                address['building'] = each['long_name']
            elif 'route' in each['types']:
                address['street'] = each['long_name']
            elif 'locality' in each ['types'] and address['country'] != 'Singapore':
                address['city'] = each['long_name']
            elif 'country' in each['types']:
                address['country'] = each['long_name']
            elif 'postal_code' in each['types']:
                address['postal'] = each['long_name']
        return address     
    
    @classmethod
    def _google_gecode_address_outformat(cls, response_data, address):
        response_data = json.loads(response_data)
        if response_data['status'] == "OK":
            response_data = response_data['results'][0]
            for each in response_data:
                if each == "place_id" and 'doc_id' not in address:
                    address['doc_id'] = "Google+"+response_data[each]
                elif each == 'geometry':
                    if 'location' in response_data[each]:
                        location = response_data[each]['location']
                        address['lat'] = location['lat']
                        address['lng'] = location['lng']
                elif each == 'formatted_address':
                    address['formatted_address']  = response_data[each]
                elif each == "address_components":
                    address = cls.parse_google_address_components(response_data[each], address)
        else:
            logging.error("Google geocode status: %s" %response_data['status'])
        return address
    
    @staticmethod
    def _mapquest_gecode_address_outformat(response_data, address):
        response_data = json.loads(response_data)
        if response_data['info']['statuscode'] == 0:
            latlng = response_data['results'][0]['locations'][0]['latLng']
            address['lat'] = latlng['lat']
            address['lng'] = latlng['lng']
            return address
        else:
            logging.error("Mapquest geocode status: %s" %response_data['info']['statuscode'] )
    
    @classmethod
    def get_geocode_address_outformat(cls, response_data, address, api_provider):
        if api_provider == "onemap":
            geo_url = cls._onemap_gecode_address_outformat(response_data, address)
        elif api_provider == "google":
            geo_url = cls._google_gecode_address_outformat(response_data, address)
        elif api_provider == "mapquest":
            geo_url = cls._mapquest_gecode_address_outformat(response_data, address)
        return geo_url        
    
    @classmethod
    def search_geocode(cls, address, api_provider):
        valid_address = cls.get_geocode_api_informat(address, api_provider)
        geo_url = cls.get_geo_url(valid_address, api_provider)
        if DEBUG:
            logging.info("geocode url : %s" %geo_url)
        
        response = urlfetch.fetch(geo_url)
        
        if DEBUG:
            logging.info('Response for geocode service: %s' %response.content)
        
        
        if response.status_code == 200:
            result_address = cls.get_geocode_address_outformat(response.content, address, api_provider)
            #get a more detailed address
            if api_provider != 'google':
                result_address = cls.search_address_details(result_address, api_provider)
            return result_address
    
    @classmethod
    def get_reverse_geo_url(cls, address, api_provider):
        latlng = "%s,%s" %(address['lat'], address['lng'])
        if api_provider == 'google':
            google_key = config.GOOGLE_KEY
            geo_url = ("https://maps.googleapis.com/maps/api/geocode/json?"
                       "latlng=%s&result_type=street_address"
                       "&key=%s"
                       ) %(latlng, google_key)
            return geo_url
        
    @classmethod
    def get_address_details_url(cls, address, api_provider):
        if api_provider == "onemap":
            address_val = cls._onemap_address_informat(address)
            onemap_token = OneMapToken.get_onemap_token()
            addr_url = ("http://www.onemap.sg/API/services.svc/basicSearch"
                          "?token=%s&searchVal=%s&returnGeom=0&rset=1&getAddrDetl=Y"
                          ) %(onemap_token,address_val)
            return addr_url          

    #same format as the geocode service
    @classmethod
    def _google_reverse_geocode_address_outformat(cls, response_data, address):
        address = cls._google_gecode_address_outformat(response_data, address)
        return address

    @classmethod
    def get_address_details_outformat(cls, response_data, address, api_provider):
        if api_provider == "onemap":
            address = cls._onemap_address_details_outformat(response_data, address)
        return address
    
    @classmethod
    def _onemap_address_details_outformat(cls, response_data, address):
        response_data = json.loads(response_data)
        if len(response_data['SearchResults']) >= 2:
            search_result = response_data['SearchResults'][1]
            address['postal'] = search_result['PostalCode']
            address_list = search_result['HBRN'].split(" ", 1)
            address['building'] = string.capwords(address_list[0], " ")
            address['street'] = string.capwords(address_list[1], " ")
            address['formatted_address']= "%s %s, Singapore %s" %(address['building'],
                                                                  address['street'],
                                                                  address['postal'])
            if 'doc_id' not in address:
                address['doc_id'] = "Singapore+%s" %address['postal']
            #logging.info(address)
        return address      
    
    @classmethod
    def search_address_details(cls, address, api_provider):
        addr_url = cls.get_address_details_url(address, api_provider)
        if DEBUG:
            logging.info("address url : %s" %addr_url)
        if addr_url:
            response = urlfetch.fetch(addr_url)
            if DEBUG:
                logging.info('Response for address details service: %s' %response.content)
                
            if response.status_code == 200:
                address = cls.get_address_details_outformat(response.content, address, api_provider)
        
        return address
