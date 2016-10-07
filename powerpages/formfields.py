# -*- coding: utf-8 -*-

from powerpages.utils.class_registry.formfields import (
    BaseRegistryItemChoiceField
)
from powerpages import page_processor_registry


class PageProcessorChoiceField(BaseRegistryItemChoiceField):
    """
    Form field intended to display keys from page_processor_registry.registry
    as it's choices
    """
    registry_instance = page_processor_registry.registry
