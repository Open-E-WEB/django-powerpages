# -*- coding: utf-8 -*-

"""
Builders for global functions to operate over given ClassRegistry instance.
"""


def register_function(registry_instance):

    def register(cls):
        """Registers new class in the registry."""
        registry_instance.register(cls)

    return register


def unregister_function(registry_instance):

    def unregister(cls):
        """Unegisters the class from the registry."""
        registry_instance.unregister(cls)

    return unregister


def as_choices_function(registry_instance):

    def as_choices():
        """
        Retrieves choice list suitable for form's ChoiceField
        from the registry.
        """
        return registry_instance.as_choices()

    return as_choices


def get_function(registry_instance):

    def get(key):
        """Retrieves class for given key from the registry"""
        return registry_instance.get(key)

    return get
