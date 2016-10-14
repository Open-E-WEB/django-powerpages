# -*- coding: utf-8 -*-

from django.utils.safestring import mark_safe
from django.contrib import admin

from powerpages.forms import PageAdminForm
from powerpages.models import Page
from powerpages.sync import PageFileDumper, SyncStatus
from powerpages.signals import page_edited


def website_link(page):
    """Link to the Page on website"""
    if not page:
        return None
    url = page.url
    url_parts = url.split('/')
    if len(url_parts) <= 1:
        styled_url = page.url
    else:
        for i in (-1, -2):
            if url_parts[i]:
                url_parts[i] = \
                    u'<span style="font-weight: bold">{0}</span>'.format(
                        url_parts[i]
                    )
                break
        styled_url = u'/'.join(url_parts)
    return mark_safe(
        u'<a href="{url}" style="font-weight: normal;">{text}</a>'.format(
            url=url, text=u'{url} &raquo;'.format(url=styled_url)
        )
    )


def sync_status(page):
    """Synchronization status of the Page"""
    if not page:
        return None
    status_parts = []
    if page.is_dirty:
        status_parts.append(
            u'<span style="color:black; font-weight:bold">'
            u'Changed in Admin!'
            u'</span>'
        )
    dump_status = PageFileDumper(page).status()
    if dump_status == SyncStatus.NO_CHANGES:
        dump_text = u'File is synced'
        dump_color = u'green'
    elif dump_status == SyncStatus.MODIFIED:
        dump_text = u'File content differs'
        dump_color = u'orange'
    elif dump_status == SyncStatus.ADDED:
        dump_text = u'File is missing'
        dump_color = u'red'
    else:  # Unknown sync status
        dump_text = u'?'
        dump_color = u'black'
    status_parts.append(
        u'<span style="color: {0}">{1}</span>'.format(
            dump_color, dump_text
        )
    )
    return mark_safe(u'<br>'.join(status_parts))


def save_page(page, user, created):
    """
    Marks the Page as "dirty" (modified in Admin),
    saves it and sends the "page edited" signal.
    """
    page.is_dirty = True
    page.save()
    page_edited.send(Page, page=page, user=user, created=created)


class PageAdmin(admin.ModelAdmin):
    """Admin interface options for Page model"""
    change_form_template = 'powerpages/admin/page_change_form.html'
    change_list_template = 'powerpages/admin/page_change_list.html'
    search_fields = (
        'url', 'alias', 'title', 'description', 'keywords', 'template'
    )
    list_display = (
        'url', 'alias', 'title', 'page_processor',
        'get_website_link', 'get_sync_status'
    )
    list_filter = ('page_processor',)
    readonly_fields = (
        'get_website_link', 'get_sync_status'
    )
    fieldsets = (
        (None, {
            'fields': (
                'get_website_link',
                'get_sync_status',
                'url',
                'alias',
            ),
        }),
        ('Metatags', {
            'fields': (
                'title',
                'description',
                'keywords',
            ),
        }),
        ('Template', {
            'fields': (
                'template',
            )
        }),
        ('Advanced', {
            'fields': (
                'page_processor',
                'page_processor_config',
            )
        }),
    )
    form = PageAdminForm

    def get_website_link(self, obj=None):
        return website_link(obj)
    get_website_link.short_description = u"URL"
    get_website_link.admin_order_field = 'url'
    get_website_link.allow_tags = True

    def get_sync_status(self, obj=None):
        return sync_status(obj)
    get_sync_status.short_description = u"Sync Status"
    get_sync_status.allow_tags = True

    def save_model(self, request, obj, form, change):
        save_page(page=obj, user=request.user, created=not change)


admin.site.register(Page, PageAdmin)
