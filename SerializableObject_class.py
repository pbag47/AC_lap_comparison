import json


class SerializableObject:
    attribute_types = {}

    def __to_json__(self):
        attributes = vars(self)
        for attribute_name, attribute_type in self.attribute_types.items():
            attributes[attribute_name] = attribute_type(attributes[attribute_name])
        attributes.update({"__class_name__": self.__class__.__name__})
        return attributes

    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, '__to_json__'):
                return obj.__to_json__()
            return json.JSONEncoder.default(self, obj)