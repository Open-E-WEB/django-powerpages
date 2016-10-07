# -*- coding: utf-8 -*-


class ClassRegistry(object):
    """Collects classes and allows to list them."""

    class RegistryError(Exception):
        """Base class for all registry errors"""
        pass

    class AlreadyRegistered(RegistryError):
        """Class is already registered"""
        pass

    class NotRegistered(RegistryError):
        """Class is not registered"""
        pass

    def __init__(self):
        self.registry = {}

    def get_key_from_class(self, cls):
        """Prepare registry key for given class"""
        return "%s.%s" % (cls.__module__.split('.')[-2], cls.__name__)

    def register(self, cls):
        """Registers new class"""
        key = self.get_key_from_class(cls)
        if key in self.registry:
            raise self.AlreadyRegistered(key)
        self.registry[key] = cls

    def unregister(self, cls):
        """Unregisters the class"""
        key = self.get_key_from_class(cls)
        if key not in self.registry:
            raise self.NotRegistered(key)
        self.registry.pop(key)

    def as_choices(self):
        """Get choice list suitable for form's ChoiceField"""
        return sorted(
            (
                (k, self.get_item_label(k, v))
                for (k, v) in self.registry.items()
            ),
            key=lambda t: t[1]
        )

    def get(self, key):
        """Retrieves class for given key"""
        if key not in self.registry:
            raise self.NotRegistered(key)
        return self.registry[key]

    def get_item_label(self, key, value):
        """Provides label for item with fallback to raw key"""
        return getattr(value, 'verbose_name', key)

    def configure_item(self, item_class, model_instance, config):
        """
        Configure registry item class per model instance and config.
        Required to use ClassRegistry together with BaseRegistryItemField.
        Default implementation creates instance of class.
        """
        return item_class(model_instance, config)
