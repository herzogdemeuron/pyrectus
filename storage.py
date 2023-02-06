"""
Code taken from https://github.com/revitron/revitron under MIT license.
Minor adjustments where made to match a more general usecase.
"""
import json
import re
import sys
import requests
import os
from log import Log
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
				Log.error('Request has failed')
				Log.error(response.json())
			return None

	def post(self, endpoint, data):
		"""
		Post data to a given enpoint.

		Args:
			endpoint (string): The endpoint
			data (dict): The data dict

		Returns:
			dict: The reponse dictionary
		"""
		response = requests.post(
		    '{}/{}'.format(self.host, endpoint),
		    headers=self._headers,
		    data=json.dumps(data),
		    allow_redirects=True
		)
		try:
			responseJson = response.json()
			return responseJson['data']
		except:
			Log.error(data)
			Log.error('Request has failed')
			Log.error(response.json())
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
	This storage driver handles storing snapshots to in Directus using the Directus API.
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
			Log.error('Invalid Directus configuration')
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
		api.post('items/{}'.format(self.collection), data)
		api.clearCache()