from django.contrib import admin
from django.utils import timezone
from .models import Client, BlogPost

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_interval_days', 'post_time', 'last_post_generated', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('last_post_generated', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Content Generation Settings', {
            'fields': ('gpt_prompt', 'post_interval_days', 'post_time')
        }),
        ('Timestamps', {
            'fields': ('last_post_generated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'created_at', 'published_at')
    list_filter = ('status', 'client', 'created_at')
    search_fields = ('title', 'content', 'client__name')
    readonly_fields = ('created_at', 'published_at')
    
    fieldsets = (
        (None, {
            'fields': ('client', 'title', 'content')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'published_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)
