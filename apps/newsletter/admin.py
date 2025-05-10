from django.contrib import admin
from .models import Newsletter, NewsletterTemplate, NewsletterTracking


@admin.register(NewsletterTemplate)
class NewsletterTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status', 'scheduled_date',
                    'sent_date', 'total_recipients', 'open_count', 'click_count')
    list_filter = ('status', 'scheduled_date', 'sent_date', 'created_at')
    search_fields = ('subject', 'content')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by',
                       'tracking_id', 'total_recipients', 'open_count', 'click_count')
    filter_horizontal = ('subscribers', 'subscriber_groups')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('subject', 'slug', 'content', 'template')
        }),
        ('Status & Scheduling', {
            'fields': ('status', 'scheduled_date', 'sent_date')
        }),
        ('Recipients', {
            'fields': ('subscribers', 'subscriber_groups', 'total_recipients')
        }),
        ('Statistics', {
            'fields': ('open_count', 'click_count', 'tracking_id')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )


@admin.register(NewsletterTracking)
class NewsletterTrackingAdmin(admin.ModelAdmin):
    list_display = ('newsletter', 'subscriber',
                    'event_type', 'created_at', 'ip_address')
    list_filter = ('event_type', 'created_at', 'newsletter')
    search_fields = ('subscriber__email', 'newsletter__subject', 'ip_address')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (None, {
            'fields': ('newsletter', 'subscriber', 'event_type')
        }),
        ('Tracking Data', {
            'fields': ('ip_address', 'user_agent', 'link_url')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
