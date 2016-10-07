# -*- coding: utf-8 -*-


from powerpages.utils.class_registry.config import Config


class ConfigurableClassRegistryItem(object):
    """Base class for classes stored in registry which may be used"""

    CONFIG_VARIABLES = ()

    def __init__(self, model_instance, config):
        self.model_instance = model_instance
        self.config = Config(self.CONFIG_VARIABLES, config)
