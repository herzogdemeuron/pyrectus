import os
from pyrectus import DirectusStorageDriver
import pprint

host = 'https://hdm-dt.directus.app/'
token = os.getenv('REVITRON_DIRECTUS_TOKEN') + '1'

config = {
    'collection': 'calc_materials',
    'host': host,
    'token': token}

def get_items():
    response = DirectusStorageDriver(config).get()
    return response

if __name__ == '__main__':
    pprint.pprint(get_items())