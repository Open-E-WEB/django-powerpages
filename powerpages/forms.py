# -*- coding: utf-8 -*-

from django import forms
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

import yaml

from powerpages.models import Page
from powerpages.widgets import SourceCodeEditor
from powerpages.sync import normalize_page_fields


class PageAdminForm(forms.ModelForm):
    """
    ModelForm for Page's ModelAdmin
    """

    class Meta:
        model = Page
        exclude = ()
        widgets = {
            'template': SourceCodeEditor,
        }

    # Model instance fields to override using cleaned data
    # during template validation:
    OVERRIDE_FIELDS = (
        'template', 'page_processor', 'page_processor_config',
        'alias', 'url'
    )

    def clean_alias(self):
        """
        Force alias to be null instead of empty string
        (protection against breaking uniqueness constraint).
        """
        alias = self.cleaned_data.get('alias')
        if not alias:
            return None
        # uniqueness validation (not handled by default, because of null=True)
        page_query = Page.objects.all()
        if self.instance and self.instance.pk:
            page_query = page_query.exclude(pk=self.instance.pk)
        try:
            page = page_query.get(alias=alias)
        except Page.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(
                'The "alias" field have to be unique or blank, but the same '
                'alias value has been found in page: %s.' % page
            )
        return alias

    def clean_page_processor_config(self):
        """Checks validity of Page processor Config, loads data from string"""
        value = (
            self.cleaned_data.get('page_processor_config') or ''
        ).strip() or None
        if value:
            try:
                value = yaml.load(value)
            except ValueError:
                raise forms.ValidationError('Invalid YAML config.')
        return value

    def clean(self):
        """Check validity of a Page template"""
        instance = self.instance
        cleaned_data = self.cleaned_data
        normalized_data = \
            cleaned_data.update(normalize_page_fields(cleaned_data))
        template = normalized_data['template']

        # we have to put changed "template" field value to the instance
        # to validate current content, not the old one
        if template:
            # Copy original attributes for further restoring:
            original_attrs = {}
            for field_name in self.OVERRIDE_FIELDS:
                original_attrs[field_name] = getattr(instance, field_name)
                setattr(instance, field_name, normalized_data.get(field_name))
            # Do the validation
            request_factory = RequestFactory()
            request = request_factory.get(instance.url)
            request.session = {}
            request.user = AnonymousUser()
            try:
                processor = instance.get_page_processor()
                processor.validate(request=request)
            finally:
                # Restore instance to state existing before the validation:
                for field_name in self.OVERRIDE_FIELDS:
                    setattr(instance, field_name, original_attrs[field_name])
        return normalized_data
