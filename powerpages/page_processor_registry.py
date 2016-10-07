# -*- coding: utf-8 -*-

from powerpages.utils.class_registry.registry import ClassRegistry
from powerpages.utils.class_registry import shortcuts


class PageProcessorRegistry(ClassRegistry):
    """Container for all PageProcessor classes"""
    pass


registry = PageProcessorRegistry()

# Module-level shortcut functions:
register = shortcuts.register_function(registry)
unregister = shortcuts.unregister_function(registry)
as_choices = shortcuts.as_choices_function(registry)
get = shortcuts.get_function(registry)
