from __future__ import annotations
from typing import Generic, TypeVar, Any, Callable, Union, get_args

import os

import yaml

import logging

logger = logging.getLogger("runner")

import re

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

T = TypeVar("T")

def check_type(value, type) -> bool:
    """Check if a value is of a given type.
    """
    
    if value is None or type == Any:
        return True
    
    if type is Union:
        return isinstance(value, get_args(type))
    else:
        return isinstance(value, type)

class ConfigurationField(Generic[T]):
    def __init__(
        self,
        type: type[T] = Any,
        required: bool = False,
        default: T | None = None,
        key: str | None = None,
    ):
        """Creates a configuration field.
        
        Arguments:
            type: The type of the field, e.g. `bool` or `int`.
                  Should be a yaml supported type. (for now, support for
                  discord type soontm)
                  Unions are supported (e.g. `Union[int, str]` or `int | str`).
            required: Whether the field is required or not.
                      If the field required but not set, an error will be logged.
            default: The default value of the field.
                     If no value is set, this value will be returned.
            key: The key of the field in the configuration file.
                 You usually don't need to set this because the configuration
                 parent sets it but you can use it if you want the field to be
                 different than the attribute name.

        Example:
        ```py
        class MyConfiguration(Configuration):
            my_field = ConfigurationField(int, required=True)
        ```

        By setting the configuration this way, you can latter access the field
        data directly like this:
        ```py
        config = MyConfiguration()
        bot.config.add_configuration_child(config)
        print(config.my_field) # prints the value of the field set in the
                               # config.yaml file
        """
        if required is True and default is not None:
            raise ValueError("You cannot set a default value for a required field")
        self.type = type
        self.required = required
        self.default = default
        self.key = key

        self.checks = []

    def __get__(self, instance: Configuration, owner=None) -> T:
        if instance is None:
            return self
        
        value = instance.raw_configuration.get(self.key, self.default)
        
        return value
    
    def check(self, callback: Callable[[T], bool]) -> ConfigurationField[T]:
        """Adds a check to the field.
        The check is a function that takes the value of the field as argument,
        the field itself and the instance for logging purposes, and returns
        True if the value is valid, False otherwise.

        Check function example:
        ```py
        def check(value, field, instance):
            if value < 0:
                logger.error("The field `%s` cannot be negative.", field.full_name(instance))
                return False
            return True
        ```
        """
        self.checks.append(callback)
        return self
    
    def process_check(self, instance: Configuration) -> bool:
        """Checks if the field is valid.
        Returns True if the field is valid, False otherwise.
        """
        check_passed = True

        if self.required and self.key not in instance.raw_configuration:
            check_passed = False
            logger.error(
                "The field `%s` is required but not present in the configuration.",
                self.full_name(instance),
            )
        
        if not check_type(self.__get__(instance), self.type):
            check_passed = False
            logger.error(
                "The field `%s` is not of the type %s (value: %s).",
                self.full_name(instance),
                self.type,
                self.__get__(instance),
            )
        
        for check in self.checks:
            if not check(self.__get__(instance), self, instance):
                check_passed = False
        
        return check_passed
    
    def full_name(self, instance: Configuration) -> str:
        """Returns the full name of the field, including the parent configuration objects.
        Needs the parent instance to work for fields.
        """
        if instance.is_child is True:
            return instance.full_name() + "." + self.key
        else:
            return self.key

class Configuration():
    __fields: dict[str, ConfigurationField] = None
    __childs: dict[str, Configuration] = None

    parent: Configuration | None = None

    namespace: str = None

    def __init_subclass__(cls) -> None:
        cls.__fields = {} # we prevent shared fields between subclasses
        cls.__childs = {}

        for key in dir(cls):
            attr = getattr(cls, key)
            if isinstance(attr, ConfigurationField):
                if attr.key is None:
                    attr.key = key
                cls.__fields[key] = attr
            elif isinstance(attr, Configuration):
                cls.__childs[key] = attr
                if attr.namespace is None:
                    attr.namespace = key

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
        
        # the namespace is only overwritten to allow setting it in the class
        if namespace is not None:
            self.namespace = namespace

        self.fields: dict[str, ConfigurationField] = {}
        
        if self.__fields is not None: # if the class has been subclassed
            self.fields.update(self.__fields)

        self.child_configurations = {}

        if self.__childs is not None: # if the class has been subclassed
            for key, child in self.__childs.items():
                child.parent = self
                self.child_configurations[key] = child
    
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
    
    def process_check(self):
        """Checks if all configuration fields are correctly set.

        This function goes through all the fields and checks if they are valid.

        Returns True if all fields are valid, False otherwise.
        """
        check_passed = True

        for field in self.fields.values():
            check_passed = check_passed and field.process_check(self)

        for child in self.child_configurations.values():
            check_passed = check_passed and child.process_check()
        
        return check_passed
    
    def full_name(self) -> str:
        """Returns the full name of the configuration, including the parent configuration objects."""
        if self.parent.is_child is True:
            return self.parent.full_name() + "." + self.namespace
        else:
            return self.namespace

def regex_check(regex: str):
    """Return a function that checks if a string matches a regex.
    """
    
    def check(value, field: ConfigurationField, instance: Configuration):
        if value is None:
            logger.error("The field `%s` cannot be None (regex check).", field.full_name(instance))
            return

        check_passed = re.match(regex, value) is not None
        if not check_passed:
            logger.error(
                "The field `%s` does not match the regex %s (value: %s).",
                instance.full_name(),
                regex,
                value,
            )
        return check_passed
    
    return check
