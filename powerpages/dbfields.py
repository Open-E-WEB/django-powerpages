# -*- coding: utf-8 -*-

from powerpages.utils.class_registry.dbfields import (
    BaseRegistryItemField, BaseRegistryItemConfigField
)
from powerpages.formfields import PageProcessorChoiceField
from powerpages import page_processor_registry


class PageProcessorField(BaseRegistryItemField):
    """
    Model field intended to store keys from page_processor_registry.registry
    """
    # Required configuration:
    registry_instance = page_processor_registry.registry
    item_accessor_method_name = 'get_page_processor'
    form_field_class = PageProcessorChoiceField
    # Item configuration (optional):
    config_accessor_method_name = 'get_page_processor_config'


class PageProcessorConfigField(BaseRegistryItemConfigField):
    """
    Model field for storing configuration of PageProcessors.
    """
    # Required configuration:
    config_accessor_method_name = 'get_page_processor_config'
