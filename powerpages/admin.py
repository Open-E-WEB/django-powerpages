# -*- coding: utf-8 -*-

from django.utils.safestring import mark_safe
from django.contrib import admin

from powerpages.forms import PageAdminForm
from powerpages.models import Page
from powerpages.sync import PageFileDumper, SyncStatus
from powerpages.signals import page_edited


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
        """Verbose version of get_url()"""
        if obj:
            splitted_url = obj.url.split("/")[:-1]
            if len(splitted_url) <= 1:
                text = u"%s &raquo;" % obj.url
            else:
                last = splitted_url[-1]
                text = u"%s &raquo;" % u"/".join(
                    splitted_url[:-1] + [(
                        u'<span style="font-weight: bold">%s</span>' % last
                    ), '']
                )
            return u'<a href="%s" style="font-weight: normal;">%s</a>' % (
                obj.url, text
            )
    get_website_link.short_description = u"URL"
    get_website_link.admin_order_field = 'url'
    get_website_link.allow_tags = True

    def get_sync_status(self, obj=None):
        """Synchronization status of Page object"""
        if obj:
            if obj.is_dirty:
                pending_info = (
                    u'<span style="color:black; font-weight:bold">'
                    u'Changed in Admin!'
                    u'</span><br/>'
                )
            else:
                pending_info = u''
            dump_status = PageFileDumper(obj).status()
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
            dump_info = u'<span style="color: {0}">{1}</span>'.format(
                dump_color, dump_text
            )
            return mark_safe(u'{0} {1}'.format(pending_info, dump_info))
    get_sync_status.short_description = u"Sync Status"
    get_sync_status.allow_tags = True

    def save_model(self, request, obj, form, change):
        """
        This will mark the page as "dirty"
        """
        obj.is_dirty = True
        obj.save()
        page_edited.send(
            self.__class__, page=obj, user=request.user, created=not change
        )


admin.site.register(Page, PageAdmin)
