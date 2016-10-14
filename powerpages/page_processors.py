# -*-coding: utf-8 -*-

import traceback

from django.forms import ValidationError
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.template import RequestContext, Context, Template
from django import http
from django.conf import settings
from django.utils.safestring import mark_safe

from powerpages.utils.class_registry.item import ConfigurableClassRegistryItem
from powerpages.utils.class_registry.config import ConfigVariable
from powerpages.settings import app_settings
from powerpages import page_processor_registry
from powerpages import cachekeys


def _get_cache_seconds(value):
    """`cache` config value converter"""
    return settings.CACHE_MIDDLEWARE_SECONDS if value is True else int(value)


class DefaultPageProcessor(ConfigurableClassRegistryItem):
    """Class responsible for rendering and validation of Pages."""

    CONFIG_VARIABLES = (
        ConfigVariable(
            'base template', converter=unicode,
            help_text="""
* name of template to be used in {% extends ... %},
* if not given parents' template is used and if page has no parent
- no base template is used.
            """,
        ),
        ConfigVariable(
            'cache', converter=_get_cache_seconds, default=0,
            help_text="""
* cache validity time in seconds,
* defaults to: `0` (no cache),
* if value is set to `true` default cache validity time is used."
(settings.CACHE_MIDDLEWARE_SECONDS).
            """,
        ),
        ConfigVariable(
            'cache for user', converter=bool, default=False,
            help_text="""
* default: `false`,
* if set to `true` page is cached per user (otherwise per language).
            """,
        ),
        ConfigVariable(
            'context processors', converter=list, default=list,
            help_text="""
* default: `[]`,
* list of context processor to be used in page template
(same as in settings.TEMPLATE_CONTEXT_PROCESSORS).
            """,
        ),
        ConfigVariable(
            'tag libraries', converter=list, default=list,
            help_text="""
* default: `[]`,
* list of tag libraries to be used in page template.
            """,
        ),
        ConfigVariable(
            'sitemap', default=True,
            help_text="""
* default: `true`
* if set to `true` page is visible in sitemap using default settings,
* if set to `false` page is not visible in sitemap,
* if set to dictionary, the following keys are used to modify
sitemap settings: `changefreq`, `lastmod`, `priority`.
            """,
        ),
        ConfigVariable(
            'headers', converter=dict, default=dict,
            help_text="""
* default: `{}`,
* dictionary with HTTP response headers.
            """,
        )
    )

    @property
    def page(self):
        """Explicit alias for model instance"""
        return self.model_instance

    def process_request(self, request, extra_context=None):
        """Main page processing logic"""
        context = self.get_rendering_context(request)
        if extra_context:
            context.update(extra_context)
        cache_key, seconds = self.get_cache_settings(request)
        if cache_key:
            content = cache.get(cache_key)
            if content is None:
                content = self.render(context)
                cache.set(cache_key, content, seconds)
        else:
            content = self.render(context)
        return self.create_response(request, content)

    def get_cache_settings(self, request):
        """
        Gives pair (cache_key, seconds) if cache is allowed for current page
        and double None otherwise
        """
        seconds = self.config.get('cache')
        if seconds:
            for_user = self.config.get('cache for user')
            if for_user:
                try:
                    user_id = request.user.id
                except AttributeError:
                    user_id = None
            else:
                user_id = None
            if user_id:
                cache_key = cachekeys.rendered_source_for_user(
                    self.page.pk, user_id
                )
            else:  # for_lang
                lang = request.LANGUAGE_CODE
                cache_key = cachekeys.rendered_source_for_lang(
                    self.page.pk, lang
                )
        else:
            cache_key, seconds = None, None
        return cache_key, seconds

    def render(self, context):
        """Render Page using given context"""
        source = self.get_template_source()
        page_template = Template(source)
        return page_template.render(context)

    def validate(self, request=None):
        """Check validity of configuration and Page template"""
        self.config.validate()
        try:
            context = self.get_validation_context(request=request)
            self.render(context)
        except:
            tb_info = traceback.format_exc()
            msg = u"""An error occurred trying to render the Page:
                <br/><pre>%s</pre>""" % tb_info
            raise ValidationError(mark_safe(msg))

    def create_response(self, request, content):
        """
        Creates HttpResponse and sets HTTP headers as defined in config.
        """
        response = http.HttpResponse(content)
        header_settings = self.config.get('headers')
        for key, value in header_settings.items():
            response[key] = value
        return response

    def get_extra_context(self, request):
        """
        Get custom context function from config and try to update
        RequestContext with it
        """
        extra_context = {}
        context_processors = self.config.get('context processors')
        for context_name in context_processors:
            context_name = context_name.split('.')
            context_module_name = ".".join(context_name[:-1])
            context_function_name = context_name[-1]
            try:
                context_module = __import__(
                    context_module_name, globals(), locals(),
                    [context_function_name, ], -1
                )
            except ImportError:
                pass
            else:
                context_function = getattr(
                    context_module, context_function_name
                )
                extra_context.update(context_function(request))
        return extra_context

    def create_request_context(self, request, data=None):
        """
        Create RequestContext for request and (optional) data.
        Update RequestContext with specified in config custom context function
        """
        data = data or {}
        extra_context = self.get_extra_context(request)
        data.update(extra_context)
        return RequestContext(request, data)

    def create_context(self, data=None):
        """Create RequestContext for request and (optional) data"""
        return Context(data)

    def get_validation_context(self, request=None):
        """Prepare context for template validation"""
        data = {}
        data['page'] = data['website_page'] = self.page
        data['page_processor'] = data['website_page_processor'] = self
        if request:
            context = self.create_request_context(request, data)
        else:
            context = self.create_context(data)
        return context

    def get_rendering_context(self, request):
        """Prepare context for page rendering"""
        data = {}
        data['page'] = data['website_page'] = self.page
        data['page_processor'] = data['website_page_processor'] = self
        return self.create_request_context(request, data)

    def get_extends_tag(self):
        """
        Prepares {% extends %} tag included
        at the beginning of template source.
        """
        base_template = self.config.get('base template')
        parent_page = self.page.parent()
        if parent_page and not base_template:
            base_template = "page/%s" % parent_page.pk
        if base_template:
            tag = u'{%% extends "%s" %%}' % base_template
        else:
            tag = u''
        return tag

    def get_load_tag(self):
        """
        Prepares {% load %} tag included at the beginning of template source.
        """
        tag_libraries = ['powerpages_tags']
        tag_libraries.extend(app_settings.TAG_LIBRARIES)
        tag_libraries.extend(self.config.get('tag libraries'))
        if tag_libraries:
            tag = u'{%% load %s %%}' % " ".join(tag_libraries)
        else:
            tag = u''
        return tag

    def get_template_source(self):
        """Prepare template source"""
        return (
            self.get_extends_tag() + self.get_load_tag() + self.page.template
        )

    def is_accessible(self):
        """Determines if Page can be accessed on URL using this processor"""
        return True


class RedirectProcessor(DefaultPageProcessor):
    """Class responsible for processing redirects."""

    CONFIG_VARIABLES = DefaultPageProcessor.CONFIG_VARIABLES + (
        ConfigVariable(
            'permanent', converter=bool, default=True,
            help_text="""
* default: `true`,
* defines if processor should use 301 or 302 HTTP response.
            """,
        ),
        ConfigVariable(
            'to alias', converter=unicode,
            help_text="""
* CMS alias of target Page.
            """,
        ),
        ConfigVariable(
            'to url', converter=unicode,
            help_text="""
* URL address of target page.
            """,
        ),
        ConfigVariable(
            'to name', converter=unicode,
            help_text="""
* name of target URL managed by Django url resolver,
* may be used together with `args` and `kwargs`.
            """,
        ),
        ConfigVariable(
            'args', converter=list, default=list,
            help_text="""
* default: `[]`,
* list of positional parameters to combine with `to name`.
            """,
        ),
        ConfigVariable(
            'kwargs', converter=dict, default=dict,
            help_text="""
* default: `{}`,
* dictionary of named parameters to combine with `to name`.
            """,
        ),
    )

    def process_request(self, request, extra_context=None):
        """Redirection processing logic"""
        try:
            location = self.get_redirect_location()
        except:
            location = '/'
            permanent = False
        else:
            permanent = self.config.get('permanent')
        response_class = (
            http.HttpResponsePermanentRedirect
            if permanent else
            http.HttpResponseRedirect
        )
        return response_class(location)

    def get_redirect_location(self):
        """Gets target location."""
        location_search_order = ('alias', 'url', 'name')
        location = None
        for method_postfix in location_search_order:
            provider = getattr(self, 'get_redirect_to_%s' % method_postfix)
            location = provider()
            if location:
                break
        return location or "/"

    def get_redirect_to_alias(self):
        """Location based on `alias` config option."""
        alias = self.config.get('to alias')
        if alias:
            page_model = self.page.__class__
            page = page_model.objects.get(alias=alias)
            return page.url

    def get_redirect_to_url(self):
        """Location based on `url` config option."""
        return self.config.get('to url')

    def get_redirect_to_name(self):
        """Location based on `name`, `args` and `kwargs` config options."""
        name = self.config.get('to name')
        if name:
            args = self.config.get('args')
            kwargs = self.config.get('kwargs')
            return reverse(name, args=args, kwargs=kwargs)

    def validate(self, request=None):
        try:
            self.get_redirect_location()
        except:
            tb_info = traceback.format_exc()
            msg = u"""An error occurred trying to render the Page:
            <br/><pre>%s</pre>""" % tb_info
            raise ValidationError(mark_safe(msg))


class NotFoundProcessor(DefaultPageProcessor):
    """
    Class responsible for 404 Page Not Found responses.
    Suitable for temporary deactivating selected pages.
    No special configuration needed.
    """

    def process_request(self, request, extra_context=None):
        """
        Raises Http404 to use django's builtin HTTP 404 Response.
        """
        raise http.Http404()

    def validate(self, request=None):
        """No need to validate anything here"""
        pass

    def is_accessible(self):
        """Determines if Page can be accessed on URL using this processor"""
        return False


page_processor_registry.register(DefaultPageProcessor)
page_processor_registry.register(RedirectProcessor)
page_processor_registry.register(NotFoundProcessor)
