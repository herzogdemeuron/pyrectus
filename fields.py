

class GenericField:
    def __init__(self, name, value):
        self.name = str(name)
        self.value = str(value)
        self.dataType = None
	

class StringField(GenericField):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.dataType = 'String'
	

class IntegerField(GenericField):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.dataType = 'Integer'
	

class FloatField(GenericField):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.dataType = 'Float'