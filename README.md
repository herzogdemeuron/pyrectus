# Pyrectus

Pyrectus is a little python helper designed to simplyfly posting data to Directus.

Example use:

    import sys
    sys.path.append("C:/pyrectus_parent_dir")
    import pyrectus

    config = {}
    config['collection'] = 'example collection'
    config['host'] = 'https://example.directus.app/'
    config['token'] = '123abc'

    data = []

    data.append(pyrectus.StringField('first name', 'Jane'))
    data.append(pyrectus.IntegerField('age', 42))
    data.append(pyrectus.FloatField('height', 5.74))
    data.append(pyrectus.BooleanField('accepted', True))
    data.append(pyrectus.JSONField('json', {"some data": "value", "key2": "value2"}))

    pyrectus.DirectusStorageDriver(config).add(data)
