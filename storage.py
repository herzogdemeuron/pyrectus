"""
Refer to LICENSE.md and LICENSE-revitron.md for copyright info.
"""
import json
import re
import sys
import requests
import os
from .log import Log
from time import time
from datetime import datetime
from abc import ABCMeta, abstractmethod


def reTokenCallback(match):
	return os.getenv(match.group(1))

def parseToken(token):
	return re.sub(r'\{\{\s*(\w+)\s*\}\}', reTokenCallback, token)


class AbstractStorageDriver:
	"""
	The abstract storage driver is the base class for all storage driver classes.
	"""
	__metaclass__ = ABCMeta

	def __init__(self, config):
		"""
		Init a new storage driver instance with a givenm configuration.

		Args:
			config (dict): The driver configuration
		"""
		self.config = config
		self.timestamp = datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')

	@abstractmethod
	def add(self, dataProviderResults, modelSize):
		"""
		Add a new snapshot.

		Args:
			dataProviderResults (list): The list of 
				:class:`revitron.analyze.DataProviderResult` objects
			modelSize (float): The local file's size in bytes
		"""
		pass


class DirectusAPI():
	"""
	The **DirectusAPI** class provides the needed tools to interact with the `Directus API <https://docs.directus.io/reference/introduction/>`_.
	"""

	def __init__(self, host, token, collection):
		"""
		Init a new API wrapper instance.

		Args:
			host (string): The API URL
			token (string): The API token that is used for authentication
			collection (string): The collection name
		"""
		self.host = host
		self.token = token
		self.collection = collection

	@property
	def _headers(self):
		return {
		    'Accept': 'application/json',
		    'Authorization': 'Bearer {}'.format(self.token),
		    'Content-Type': 'application/json'
		}

	def get(self, endpoint, log=True):
		"""
		Get data from a given endpoint.

		Args:
			endpoint (string): The Directus API endpoint
			log (bool, optional): Enable logging. Defaults to True.

		Returns:
			dict: The reponse dictionary
		"""
		response = requests.get(
		    '{}/{}'.format(self.host, endpoint),
		    headers=self._headers,
		    allow_redirects=True
		)
		try:
			responseJson = response.json()
			return responseJson['data']
		except:
			if log:
				Log().error('Request has failed')
				Log().error(response.json())
			return None

	def post(self, endpoint, data, fields=None):
		"""
		Post data to a given enpoint.

		Args:
			endpoint (string): The endpoint
			data (dict): The data dict
			fields (list, optional): The list of fields to return. Defaults to None.

		Returns:
			dict: The reponse dictionary
		"""
		url = '{}/{}'.format(self.host, endpoint)
		if fields:
			url += '?fields={}'.format(','.join(fields))
		response = requests.post(
		    url,
		    headers=self._headers,
		    data=json.dumps(data),
		    allow_redirects=True
		)
		Log().info('Directus status code: {}'.format(response.status_code))
		try:
			responseJson = response.json()
			return responseJson['data']
		except:
			Log().error(data)
			Log().error('Request has failed')
			Log().error(response.json())
			return None
	
	def patch(self, endpoint, data, fields=None):
		"""
		patch data to a given enpoint to update data.

		Args:
			endpoint (string): The endpoint
			data (dict): The data dict
			fields (list, optional): The list of fields to return. Defaults to None.

		Returns:
			dict: The reponse dictionary
		"""
		url = '{}/{}'.format(self.host, endpoint)
		if fields:
			url += '?fields={}'.format(','.join(fields))
		response = requests.post(
		    url,
		    headers=self._headers,
		    data=json.dumps(data),
		    allow_redirects=True
		)
		Log().info('Directus status code: {}'.format(response.status_code))
		try:
			responseJson = response.json()
			return responseJson['data']
		except:
			Log().error(data)
			Log().error('Request has failed')
			Log().error(response.json())
			return None

	def collectionExists(self):
		"""
		Test whether a collection exists.	 

		Returns:
			bool: True if the collection exists
		"""
		return self.get('collections/{}'.format(self.collection), False) is not None

	def getFields(self):
		"""
		Get the fields list of a collection.

		Returns:
			list: The list of fields
		"""
		fields = []
		data = self.get('fields/{}'.format(self.collection))
		if data:
			for item in data:
				fields.append(item['field'])
		return fields

	def clearCache(self):
		"""
		Clear the Directus cache.

		Returns:
			dict: The response data
		"""
		return requests.post(
		    '{}/{}'.format(self.host, 'utils/cache/clear'), headers=self._headers
		)

	def createCollection(self):
		"""
		Create the collection.

		Returns:
			dict: The response data
		"""
		return self.post(
		    'collections', {
		        'collection': self.collection, 'schema': {}, 'meta': {
		            'icon': 'timeline'
		        }
		    }
		)

	def createField(self, name, dataType):
		"""
		Create a field in the collection.

		Args:
			name (string): The field name
			dataType (string): The data type for the field

		Returns:
			dict: The response data
		"""
		data = {
		    'field': name,
		    'type': dataType.replace('real', 'float'),
		    'schema': {},
		    'meta': {
		        'icon': 'data_usage'
		    }
		}
		return self.post('fields/{}'.format(self.collection), data)


class DirectusStorageDriver(AbstractStorageDriver):
	"""
	This storage driver handles storing data to in Directus using the Directus API.
	"""

	def __init__(self, config):
		"""
		Init a new Directus storage driver instance with a given configuration.

		Args:
			config (dict): The driver configuration
		"""
		try:
			collection = '{}'.format(
			    re.sub(r'[^a-z0-9]+', '_', config['collection'].lower())
			)
			host = config['host'].rstrip('/')
			token = parseToken(config['token'])
		except:
			Log().error('Invalid Directus configuration')
			sys.exit(1)
		self.api = DirectusAPI(host, token, collection)
		self.collection = collection
		self.timestamp = datetime.fromtimestamp(time()).strftime('%Y-%m-%dT%H:%M:%S')

	def _createMissingFields(self, dataProviderResults):
		remoteFields = self.api.getFields()
		if 'timestamp' not in remoteFields:
			self.api.createField('timestamp', 'timestamp')
		for item in dataProviderResults:
			if item.name not in remoteFields:
				self.api.createField(item.name, item.dataType)

	def add(self, dataProviderResults):
		"""
		Send a POST request to the Directus API in order store a snapshot

		Args:
			dataProviderResults (list): The list of 
				:class:`pyrectus.fields.GenericField` objects
		"""
		api = self.api
		api.clearCache()
		rowId = 1
		remoteItems = api.get('items/{}?sort=-id'.format(self.collection), log=False)
		if remoteItems:
			maxId = max(row['id'] for row in remoteItems)
			rowId = maxId + 1
		if not api.collectionExists():
			api.createCollection()
		self._createMissingFields(dataProviderResults)
		data = {}
		data['id'] = rowId
		data['timestamp'] = self.timestamp
		for item in dataProviderResults:
			data[item.name] = item.value
		response = api.post('items/{}'.format(self.collection), data)
		api.clearCache()
		return response
	
	def add_many(self, dataProviderResultList, fields=None):
		"""
		Send a POST request to the Directus API to store multiple items in a batch.
		
		Args:
			dataProviderResultList (list of list): Each inner list contains 
				:class:`pyrectus.fields.GenericField` objects representing one record.
		"""
		api = self.api
		api.clearCache()

		# Prepare the data for batch insertion
		data_list = []
		for dataProviderResult in dataProviderResultList:
			item_data = {}
			for item in dataProviderResult:
				item_data[item.name] = item.value  # Assuming `item.value` extracts the correct value
			data_list.append(item_data)

		response = api.post('items/{}'.format(self.collection), data_list, fields=fields)
		api.clearCache()
		return response
	
	def update_many(self, dataProviderResultList, fields=None):
		"""
		Send a PATCH request to the Directus API to update multiple items in a batch.
		
		Args:
			dataProviderResultList (list of list): Each inner list contains 
				:class:`pyrectus.fields.GenericField` objects representing one record.
		"""
		api = self.api
		api.clearCache()

		# Prepare the data for batch insertion
		data_list = []
		for dataProviderResult in dataProviderResultList:
			item_data = {}
			for item in dataProviderResult:
				item_data[item.name] = item.value  # Assuming `item.value` extracts the correct value
			data_list.append(item_data)

		response = api.patch('items/{}'.format(self.collection), data_list, fields=fields)
		api.clearCache()
		print("Response from Directus:", response)  # Print the response to debug
		return response

	def get_items_count(self):
		"""
		Get the count of items in a specified collection.
		"""
		response = self.api.get('items/{}?aggregate[count]=*'.format(self.collection))
		try:
			count = response[0]['count']
			return int(count)
		except:
			return None
	
	def get_items(self, filters={}, limit=1000, fields=None):
		"""
		Get data from a collection.

		Args:
			filters (dict, optional): The filter dict. Defaults to {}.
			limit (int, optional): The limit of items to return. Defaults to 100.
			fields (list, optional): The list of fields to return. Defaults to None.

		Returns:
			list: The list of items
		"""
		query_params = '?limit={}'.format(limit)

		for key, value in filters.items():
			query_params += '&filter[{}][_eq]={}'.format(key, value)
		
		if fields:
			fields_param = ','.join(fields)
			query_params += '&fields={}'.format(fields_param)

		response = self.api.get('items/{}{}'.format(self.collection, query_params))
		return response
