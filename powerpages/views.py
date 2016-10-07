# -*- coding: utf-8 -*-

from django import http
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache

from powerpages.models import Page
from powerpages import sitemap_config
from powerpages import cachekeys


def page(request, path):
    """Page processing view"""
    # ensure that path starts and ends with "/"
    if not path.startswith("/"):
        path = "/" + path
    # redirect to equivalent page with ending slash
    # if path doesn't end with slash and it's not a file name:
    if not path.endswith("/") and '.' not in path.split('/')[-1]:
        return http.HttpResponsePermanentRedirect(path + "/")
    matching_pages = Page.objects.all().filter(url=path)
    try:
        page_obj = matching_pages[0]
    except IndexError:
        raise http.Http404
    page_processor = page_obj.get_page_processor()
    return page_processor.process_request(request)


@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_switch_edit_mode(request):
    """Turns website edit mode ON / OFF"""
    key = 'WEBSITE_EDIT_MODE'
    if key in request.session:
        del request.session[key]
    else:
        request.session[key] = True
    referrer = request.META.get('HTTP_REFERER')
    if referrer == request.path_info:
        referrer = None
    return http.HttpResponseRedirect(referrer or '/')


def sitemap(request):
    """Simple XML sitemap view."""
    sitemap_content = cache.get(cachekeys.SITEMAP_CONTENT)
    if sitemap_content is None:
        sitemap_content = render_to_string(
            'powerpages/sitemap.xml',
            {'urlset': sitemap_config.sitemaps.urls(request)},
            context_instance=RequestContext(request)
        )
        cache.get(cachekeys.SITEMAP_CONTENT, sitemap_content)
    return http.HttpResponse(sitemap_content, content_type='application/xml')
