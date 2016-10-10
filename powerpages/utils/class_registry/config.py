# -*- coding: utf-8 -*-

from django.core.validators import ValidationError


def default_converter(value):
    return value


class UndefinedVariable(Exception):
    """Attempt to use variable missing from the specification."""
    pass


class Config(object):
    """Container for variables' definitions and applied values"""

    def __init__(self, variables, data):
        self.variable_by_name = {}
        for variable in variables:
            self.variable_by_name[variable.name] = variable
        self.data = data

    def get(self, name):
        """Retrieves value from config"""
        if name not in self.variable_by_name:
            raise UndefinedVariable(name)
        variable = self.variable_by_name[name]
        return variable.get_value(self.data)

    def validate(self):
        """
        Checks the data against validation settings for each variable.
        """
        errors = []
        for name, variable in self.variable_by_name.items():
            try:
                variable.validate_value(self.data)
            except ValidationError as e:
                for message in e.messages:
                    errors.append(u'{0}: {1}'.format(name, message))
        if errors:
            raise ValidationError(errors)


class ConfigVariable(object):
    """Specification of config variable"""

    default_error_messages = {
        'required': u'This variable is required.',
        'invalid': u'Enter a valid value.',
        'unable_to_process':
        u'Unable to process variable (%(exc_type)s: %(exc_message)s).',
        'invalid_choice': u'%(value)s is not one of the available choices.',
    }

    def __init__(self, name, converter=None, default=None, choices=None,
                 multiple=False, required=False, validators=None,
                 error_messages=None, help_text=''):
        if converter and choices:
            raise ValueError(
                'Options `converter` and `choices` are exclusive.'
            )
        self.name = name
        self.converter = converter if converter else default_converter
        self.default = default
        self.choices = choices
        self.multiple = multiple
        self.required = required
        self.help_text = help_text
        self.validators = validators or []
        # Error message gathering:
        messages = {}
        for c in reversed(self.__class__.__mro__):
            messages.update(getattr(c, 'default_error_messages', {}))
        messages.update(error_messages or {})
        self.error_messages = messages

    def get_default_value(self):
        """Retrieves default value with optional validation"""
        value = self.default
        if callable(value):  # may be callable
            value = value()
        return value

    def get_single_value(self, raw_config_value):
        """Retrieves single value"""
        if self.choices:
            # Choices applied:
            # Map the value using choices, with fallback to the default
            # when value is not in available choices
            reversed_choice_dict = dict((v, k) for (k, v) in self.choices)
            try:
                value = reversed_choice_dict[raw_config_value]
            except KeyError:
                raise ValidationError(
                    self.error_messages['invalid_choice'] % {
                        'value': raw_config_value
                    }
                )
        else:
            # Converter applied:
            # Map the value using converter,
            # with fallback to the default when conversion fails
            try:
                value = self.converter(raw_config_value)
            except Exception as e:
                raise ValidationError(
                    self.error_messages['unable_to_process'] % {
                        'exc_type': e.__class__.__name__,
                        'exc_message': e.message
                    }
                )
        if callable(value):  # may be callable
            value = value()
        return value

    def get_multiple_values(self, raw_config_values):
        """Retrieves multiple values"""
        try:
            iter(raw_config_values)
        except TypeError as e:
            raise ValidationError(
                self.error_messages['unable_to_process'] % {
                    'exc_type': e.__class__.__name__,
                    'exc_message': e.message
                }
            )
        return [
            self.get_single_value(raw_config_value)
            for raw_config_value in raw_config_values
        ]

    def get_value(self, data):
        """Retrieves value from data with fallback to defaults"""
        # Retrieve raw config value, with fallback to default
        # when value is not defined
        try:
            raw_config_value = data[self.name]
        except KeyError:
            value = self.get_default_value()
        else:
            try:
                if self.multiple:
                    value = self.get_multiple_values(raw_config_value)
                else:
                    value = self.get_single_value(raw_config_value)
            except ValidationError:
                value = self.get_default_value()
        return value

    def validate_value(self, data):
        """Checks the data against validation settings this variable."""
        value = self.run_basic_validation(data)
        self.run_validators(value)

    def run_basic_validation(self, data):
        """
        Validates presence of variable and conversion.
        Returns converted value on success.
        """
        # Check presence of value
        try:
            raw_config_value = data[self.name]
        except KeyError:
            if self.required:
                raise ValidationError(self.error_messages['required'])
            value = self.get_default_value()
        else:
            # Validation errors are passed:
            if self.multiple:
                value = self.get_multiple_values(raw_config_value)
            else:
                value = self.get_single_value(raw_config_value)
        return value

    def run_validators(self, value):
        """
        Checks value retrieved by run_basic_validation()
        against all validators.
        Copied from `django.forms.fields.Field.run_validators`.
        """
        errors = []
        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as e:
                if hasattr(e, 'code') and e.code in self.error_messages:
                    message = self.error_messages[e.code]
                    if e.params:
                        message = message % e.params
                    errors.append(message)
                else:
                    errors.extend(e.messages)
        if errors:
            raise ValidationError(errors)
