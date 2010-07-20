
import urllib2
from urllib import quote_plus, urlencode
from lxml import etree as et

from constants import *

class Request():
	
	def __init__(self, collection, index, value, **kwargs):
		
		# Construct the API address
		self.url = ''
		
		# Are arguments valid?
		if self.__validate(collection, index, value, kwargs):
			self.collection = collection
			self.index = index
			self.value = value
			self.params = kwargs
			
			self.__construct_url()


	def __construct_url(self):
		'''Constructs the URL to call'''
		
		if self.collection and self.index and self.value:
			# Check for an API key
			# API keys can be specified in constants.py in the package or passed into the Request constructor
			if APIKEY or (self.params.has_key('apikey') and self.params['apikey']):
				self.url = "%(apibase)s/api/%(collection)s.xml?access_key=%(key)s&index1=%(index)s&value1=%(value)s" % {
								'apibase': APIBASE,
								'collection': self.collection,
								'key': APIKEY if APIKEY != "" else self.params['apikey'],
								'index': self.index,
								'value': quote_plus(self.value)
							}
							
				# Tack on additional query params if they exist			
				if self.params:
					self.url = "%s&%s" % (self.url, urlencode(self.params))
					
			else:
				raise ISBNdbAPIException("API key not found")

	def __validate(self, collection, index, value, kwargs=None):
		''' Check if collection and index are valid'''
		
		if API.has_key(collection) and index in API[collection]['request']:		
			if kwargs.has_key('results') and kwargs['results'] not in API[collection]['results']:
				raise ISBNdbAPIException("Requested parameters do not match API model")
			
			return True
		
		raise ISBNdbAPIException("Requested parameters do not match API model")


	def extend_url(self, params):
		self.params.update(params)
		self.__construct_url()
		

	def send(self):
		'''Perform the request, returning the results'''
		return urllib2.urlopen(self.url)

		
	def response(self):
		'''Returns the Reponse object for this Request'''
		return Response(self)
		

class Response():
	'''Response from the ISBNdb.com server'''
	
	def __init__(self, request):
	
		self.__request = None
		self.__pages = []
		self.__curr_page = None
		self.__curr_page_num = 0
		self.__pages_total = 0
		self.__results_total = 0
		self.__raw_response = ""

		self.results = []	
	
		self.__request = request
		self.__set_self()	
		

	def __set_self(self):
		# Send the request and read the reponse
		self.__raw_response = self.__request.send().read()
		
		self.__curr_page = et.fromstring(self.__raw_response)
		self.__pages.append(self.__curr_page)
		
		# list() gives us a list of descendents of root element, ie. in this case <ISBNdb>
		# So we take the first child and extract some info from it
		page_attribs = list(self.__curr_page)[0].attrib
		self.__curr_page_num = int(page_attribs['page_number'])

		
		# The following bits should only be run the first time this Response
		# has been constructed out of a Request

		if self.__results_total == 0:
			self.__results_total = int(page_attribs['total_results'])
		
		if self.__pages_total == 0:
			self.__pages_total = self.__results_total / int(page_attribs['page_size'])
			
			# If it's not a clean division, add one more page for the remainder
			if self.__results_total % int(page_attribs['page_size']):
				self.__pages_total = self.__pages_total + 1
		
	
	def raw(self):
		return self.__raw_response

	def has_more(self):
		return True if self.__curr_page_num < self.__pages_total else False


	def current_page(self):
		if self.__curr_page is not None:
			self.__curr_page = et.fromstring(self.__raw_response)

		return self.__curr_page
		
	
	def next_page(self):
		if self.__curr_page_num < self.__pages_total:
			self.__request.extend_url({'page_number': self.__curr_page_num + 1}) # Set our request to point to the next page
			self.__set_self()
			return self.current_page()			
			
		else:
			return None


class ISBNdbAPIException(Exception):
	pass