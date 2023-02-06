

class GenericField:
    """
    Generic data class.
    """
    def __init__(self, name, value):
        self.name = str(name)
        self.value = str(value)
        self.dataType = None
	

class StringField(GenericField):
    """
    A class holding string information.
    """
    def __init__(self, name, value):
        """
        Inits an new 'StringField' instance.

        Args:
            name (str): The field name
            value (str): The filed value
        """
        super().__init__(name, value)
        self.dataType = 'string'
	

class IntegerField(GenericField):
    """
    Inits an new 'IntegerField' instance.

    Args:
        name (str): The field name
        value (str): The filed value
    """
    def __init__(self, name, value):
        super().__init__(name, value)
        self.dataType = 'integer'
	

class FloatField(GenericField):
    """
    Inits an new 'FloatField' instance.

    Args:
        name (str): The field name
        value (str): The filed value
    """
    def __init__(self, name, value):
        super().__init__(name, value)
        self.dataType = 'float'