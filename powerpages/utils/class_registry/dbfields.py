# -*- coding: utf-8 -*-

import yaml

from django import forms
from django.db import models
from django.core.serializers.pyyaml import DjangoSafeDumper


class BaseRegistryItemField(models.CharField):
    """
    Model field intended to store keys from given class registry
    """
    # Required configuration:
    registry_instance = None
    item_accessor_method_name = None
    form_field_class = None
    # Item configuration (optional):
    config_accessor_method_name = None

    def formfield(self, form_class=None, **kwargs):
        if form_class is None:
            form_class = self.form_field_class
        kwargs['form_class'] = form_class
        kwargs['widget'] = forms.Select
        return super(BaseRegistryItemField, self).formfield(**kwargs)

    def contribute_to_class(self, cls, name, *args, **kwargs):
        """Apply get_page_processor method to model class"""

        def get_registry_item(model_instance):
            key = getattr(model_instance, name)
            if key:
                item_class = self.registry_instance.get(key)
                if self.item_accessor_method_name:
                    item_config = getattr(
                        model_instance, self.config_accessor_method_name,
                        lambda: {}
                    )()
                else:
                    item_config = None
                # Class registry is responsible for configuration
                # (eg. instantiation) of items
                return self.registry_instance.configure_item(
                    item_class, model_instance, item_config
                )

        super(
            BaseRegistryItemField, self
        ).contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, self.item_accessor_method_name, get_registry_item)


class BaseRegistryItemConfigField(models.TextField):
    """
    Model field for storing configuration in database as YAML documents.
    Based on:
    https://github.com/datadesk/django-yamlfield
    """
    # Required configuration:
    config_accessor_method_name = None

    def from_db_value(self, value, expression, connection, context):
        """
        Convert our YAML string to a Python object
        after we load it from the DB.
        """
        if value == "":
            return None
        try:
            if isinstance(value, basestring):
                return yaml.load(value)
        except ValueError:
            pass
        return value

    def get_db_prep_save(self, value, connection):
        """
        Convert our Python object to a string of YAML before we save.
        """
        if not value or value == "":
            return ""
        if isinstance(value, (dict, list)):
            value = yaml.dump(
                value, Dumper=DjangoSafeDumper, default_flow_style=False
            )
        return super(BaseRegistryItemConfigField, self).get_db_prep_save(
            value, connection=connection
        )

    def value_from_object(self, obj):
        """
        Returns the value of this field in the given model instance.

        We need to override this so that the YAML comes out properly formatted
        in the admin widget.
        """
        value = getattr(obj, self.attname)
        if not value or value == "":
            return value
        return yaml.dump(
            value, Dumper=DjangoSafeDumper, default_flow_style=False
        )

    def contribute_to_class(self, cls, name, *args, **kwargs):
        """Apply get_page_processor_config method to model class"""

        def get_registry_item_config(model_instance):
            return getattr(model_instance, name) or {}

        super(
            BaseRegistryItemConfigField, self
        ).contribute_to_class(cls, name, *args, **kwargs)
        setattr(
            cls, self.config_accessor_method_name, get_registry_item_config
        )
