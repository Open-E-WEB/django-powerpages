# -*- coding: utf-8 -*-

from django.conf.urls import url
from powerpages import views


urlpatterns = [
    url('^powerpages-admin/switch-edit-mode/$', views.admin_switch_edit_mode,
        name='switch_edit_mode'),
    url(r'^sitemap\.xml', views.sitemap, name='sitemap'),
    url('^(?P<path>[\S\s]*)$', views.page, name='page')
]
