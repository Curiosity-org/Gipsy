from __future__ import annotations
from typing import Generic, Iterable, TypeVar, Any, Callable, Union, get_args

import os
import yaml

import logging

logger = logging.getLogger("runner")

import re

def extend(object_1: dict, object_2: dict):
    """Extend object_1 with object_2,overwriting keys in object_1 if they exist
    in object_2.
    Lists are extended, not overwritten.
    If the type of a key in object_2 is different from the type of the same key
    in object_1, the key in object_1 is overwritten.
    """
    for key, value in object_2.items():
        if isinstance(value, dict): # append recursively dict to dict
            node = object_1.setdefault(key, {})
            if isinstance(node, dict):
                extend(node, value)
            else: # if the key in the origin dict is not the same type, overwrite it
                object_1[key] = value
        elif isinstance(value, list):
            node = object_1.setdefault(key, [])
            if isinstance(node, list):
                node.extend(value)
            else: # if the key in the origin dict is not the same type, overwrite it
                object_1[key] = value
        else:
            object_1[key] = value

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
        
        return self.get(instance)
    
    def check(self, callback: Callable[[T], bool]) -> ConfigurationField[T]:
        """Adds a check to the field.
        The check is a function that takes the value of the field as argument,
        the field itself and the instance for logging purposes, and returns
        `True` if the value is valid, `False` otherwise.

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
    
    def process_check(
        self,
        instance: Configuration,
        index: int = None,
    ) -> bool:
        """Checks if the field is valid.
        Returns True if the field is valid, False otherwise.
        """
        check_passed = True

        if index is None:
            if self.required and self.key not in instance.raw_configuration:
                check_passed = False
                logger.error(
                    "The field `%s` is required but not present in the configuration.",
                    self.full_name(instance),
                )
            
        if not check_type(self.get(instance, index), self.type):
            check_passed = False
            if index is None:
                logger.error(
                    "The field `%s` is not of the type %s (value: %s).",
                    self.full_name(instance),
                    self.type,
                    self.get(instance, index),
                )
            else:
                logger.error(
                    "The field `%s` is not of the type %s at index %i (value: %s).",
                    self.full_name(instance),
                    self.type,
                    index,
                    self.get(instance, index),
                )
        
        for check in self.checks:
            if not check(self.get(instance, index), self, instance):
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
        
    def get(self, instance: Configuration, index: None | int = None) -> T:
        """Returns the field value stored in the parent class.

        If `index` is specified, the item considere that the direct parent is
        a list and get the item from the specified index from the list stored
        in parent.
        """
        
        if index is None:
            return instance.raw_configuration.get(self.key, self.default)
        else:
            # no need to return a default value, ConfigurationList handles it
            return instance.raw_configuration[index]

class ConfigurationListField(Generic[T]):
    def __init__(
        self,
        child: ConfigurationField[T],
        required: bool = False,
        default: list[T] | None = None,
        key: str | None = None,
    ):
        if default is not None and required is not None:
            raise ValueError("You cannot set a default value for a required field")
        
        self.child = child
        self.required = required
        self.default = default
        self.key = key

        self.checks = []
    
    def __get__(
        self,
        instance: Configuration,
        owner=None,
    ) -> ConfigurationListProxy[T]:
        if instance is None:
            return self
        
        return ConfigurationListProxy(self, instance)

    def get_child(self) -> ConfigurationField:
        return self.__dict__.get('child')
    
    def full_name(self, instance: Configuration) -> str:
        """Returns the full name of the field, including the parent
        configuration objects.
        Needs the parent instance to work for list fields.
        """
        if instance.is_child is True:
            return instance.full_name() + "." + self.key
        else:
            return self.key
    
    def process_check(self, instance: Configuration) -> bool:
        """Checks if the field is valid.
        Returns True if the field is valid, False otherwise.
        """
        check_passed = True

        if self.required and self.key not in instance.raw_configuration:
            check_passed = False
            logger.error(
                "The list field `%s` is required but not present in the"\
                    "configuration.",
                self.full_name(instance),
            )
        
        proxy = self.__get__(instance)

        for check in self.checks:
            if not check(proxy.raw_configuration, self, instance):
                check_passed = False
        
        for index in range(len(proxy.raw_configuration)):
            if not self.get_child().process_check(proxy, index):
                check_passed = False
        
        return check_passed
    
    def check(self, callback: Callable[[T], bool]) -> ConfigurationField[T]:
        """Adds a check to the field.
        The check is a function that takes the raw data contained in the
        configuration, the field itself and the instance for logging purposes,
        and returns `True` if the value is valid, `False` otherwise.

        If you want to check the values contained in the list, it is preferable
        to add the check to the type field.

        Check function example:
        ```py
        def check(raw_value, field, instance):
            if len(raw_value) < 2:
                logger.error(
                    "You need at lease 2 values in the field `%s`.",
                    field.full_name(instance),
                )
                return False
            return True
        ```
        """
        self.checks.append(callback)
        return self

class ConfigurationListProxy(Generic[T]):
    def __init__(
        self,
        field: ConfigurationListField,
        parent: Configuration,
    ):
        self.field = field
        self.parent = parent
    
    def __getitem__(self, index: int) -> T:
        if isinstance(index, int): # index
            return self.field.get_child().get(self, index)
        elif isinstance(index, slice): # slice for example list[1:3]
            raise NotImplementedError()
    
    @property
    def raw_configuration(self) -> list:
        return self.parent.raw_configuration.get(self.field.key, [])
    
    def __iter__(self):
        for index in range(len(self.raw_configuration)):
            yield self[index]
    
    def __len__(self):
        return len(self.raw_configuration)
    
    def __repr__(self) -> str:
        """Render the object in a string.
        This function is not optimized, you should only use it for live debug
        purposes.
        """
        return repr(list(self))

    # placeholders for future update

    def __setitem__(self, index: int, value: T):
        raise NotImplementedError
    
    def __delitem__(self, index: int):
        raise NotImplementedError
    
    def append(self, object: T):
        raise NotImplementedError
    
    def count(self, object: T) -> int:
        raise NotImplementedError
    
    def clear(self):
        raise NotImplementedError
    
    def extend(self, iterable: Iterable[T]):
        raise NotImplementedError
    
    def index(self, value: T, start: int, stop: int) -> int:
        raise NotImplementedError
    
    def insert(self, index: int, object: T):
        raise NotImplementedError
    
    def pop(self, index=-1) -> T:
        raise NotImplementedError
    
    def remove(self, value: T):
        raise NotImplementedError
    
    def reverse(self):
        raise NotImplementedError
    
    def sort(self, key=None, reverse=False):
        raise NotImplementedError

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
            if isinstance(attr, (ConfigurationField, ConfigurationListField)):
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
        
        if raw_config is not None: # ignore empty files
            extend(self._raw_configuration, raw_config)
    
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
