from __future__ import annotations
from typing import Generic, TypeVar, Any

import os

import yaml

def append_dict(dict1: dict, dict2: dict):
    """Append dict2 to dict1, overwriting keys in dict1 if they exist in dict2.
    Lists are extended, not overwritten.
    If the type of a key in dict2 is different from the type of the same key in
    dict1, the key in dict1 is overwritten.
    """
    for key, value in dict2.items():
        if isinstance(value, dict): # append recursively dict to dict
            node = dict1.setdefault(key, {})
            if isinstance(node, dict):
                append_dict(node, value)
            else: # if the key in the origin dict is not the same type, overwrite it
                dict1[key] = value
        elif isinstance(value, list):
            node = dict1.setdefault(key, [])
            if isinstance(node, list):
                node.extend(value)
            else: # if the key in the origin dict is not the same type, overwrite it
                dict1[key] = value
        else:
            dict1[key] = value

T = TypeVar("T", )

class ConfigurationField(Generic[T]):
    def __init__(
        self,
        type: type[T] = Any,
        default: T | None = None,
        key: str | None = None,
    ):
        self.type = type
        self.default = None
        self.key = key

    def __get__(self, instance: Configuration, owner=None) -> T:
        if instance is None:
            return self
        
        value = instance.raw_configuration.get(self.key, self.default)
        
        return value

class Configuration():
    __fields = {}

    parent: Configuration | None = None

    def __init_subclass__(cls) -> None:
        for attr_key in dir(cls):
            attr = getattr(cls, attr_key)
            if isinstance(attr, ConfigurationField):
                if attr.key is None:
                    attr.key = attr_key
                cls.__fields[attr_key] = attr

    def __init__(
        self,
        namespace: str | None = None,
        is_child: bool = True,
    ):
        self.is_child = is_child

        if not self.is_child:
            if namespace is not None:
                raise ValueError("The root configuration must not have a namespace.")
            self._raw_configuration = {}
        else:
            self._raw_configuration = None
        
        self.namespace = namespace

        self.fields = {}
        
        self.fields.update(self.__fields)

        self.child_configurations = {}
    
    @property
    def raw_configuration(self):
        if self.is_child:
            return self.parent.raw_configuration.get(self.namespace, {})
        else:
            return self._raw_configuration
    
    def load(self, file: os.PathLike):
        """Append the configuration from a file to the current loaded
        configuration.
        
        This function manages overwrites using the `append_dict` function.
        """

        if self.is_child:
            raise NotImplementedError("Child configurations cannot load files.")

        with open(file, 'r') as config_file:
            raw_config = yaml.load(config_file, Loader=yaml.FullLoader)

        append_dict(self._raw_configuration, raw_config)
    
    def __getitem__(self, index):
        if index in self.child_configurations:
            return self.child_configurations[index]
        elif index in self.fields:
            return self.fields[index].__get__(self)
        elif index in self.raw_configuration:
            return self.raw_configuration[index]
        else:
            raise KeyError(f"Configuration field '{index}' does not exist.")
    
    def __setitem__(self, index, value):
        raise NotImplementedError("Configuration fields are read only.")
    
    def __delitem__(self, index, value):
        raise NotImplementedError("Configuration fields are read only.")
    
    def add_configuration_child(self, configuration: Configuration):
        if configuration.namespace is None:
            raise ValueError("The child configuration must have a namespace.")
        
        if configuration.namespace in self.child_configurations:
            raise ValueError(f"The namespace '{configuration.namespace}' is already used.")
        
        configuration.parent = self
        self.child_configurations[configuration.namespace] = configuration
    
    def add_configuration_field(self, field: ConfigurationField):
        if field.name in self.fields:
            raise ValueError(f"The field '{field.name}' is already used.")
        
        field.parent = self
        self.fields[field.name] = field

if __name__ == "__main__":
    # géré par le cœur
    config = Configuration(is_child=False)
    config.load("test.yaml")

    class DiscordConfiguration(Configuration):
        token = ConfigurationField(str)
    
    test = DiscordConfiguration("discord")
    config.add_configuration_child(test)

    print(test.token)
