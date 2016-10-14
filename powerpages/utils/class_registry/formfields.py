# -*- coding: utf-8 -*-

from django.forms.fields import ChoiceField


class BaseRegistryItemChoiceField(ChoiceField):
    """
    Form field intended to display keys from given class registry
    as it's choices
    """
    # Required configuration:
    registry_instance = None

    def __init__(self, choices=(), *args, **kwargs):
        kwargs.pop('max_length', None)
        # pass choices as callable to defer evaluation:
        choices = self.registry_instance.as_choices
        super(BaseRegistryItemChoiceField, self).__init__(
            choices, *args, **kwargs
        )
