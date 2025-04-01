from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from .models import Client, BlogPost, ToneOfVoice, ToneOfVoiceExample
from .tasks import generate_blog_posts

class ToneOfVoiceExampleInline(admin.TabularInline):
    model = ToneOfVoiceExample
    extra = 1
    fields = ('title', 'content')

@admin.register(ToneOfVoice)
class ToneOfVoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at', 'example_count')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ToneOfVoiceExampleInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def example_count(self, obj):
        return obj.example_posts.count()
    example_count.short_description = "Number of Examples"

class BlogPostInline(admin.TabularInline):
    model = BlogPost
    extra = 0
    readonly_fields = ('title', 'status', 'created_at', 'published_at', 'view_content')
    fields = ('title', 'status', 'created_at', 'published_at', 'view_content')
    ordering = ('-created_at',)
    can_delete = False
    max_num = 0
    
    def view_content(self, obj):
        if obj.id:
            url = reverse('admin:blogs_blogpost_change', args=[obj.id])
            return format_html('<a href="{}">View Full Post</a>', url)
        return "-"
    view_content.short_description = "Content"

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'tone_of_voice', 'post_interval_days', 'post_time', 'last_post_generated', 'is_active', 'created_at', 'view_posts')
    list_filter = ('is_active', 'tone_of_voice')
    search_fields = ('name', 'tone_of_voice__name')
    readonly_fields = ('last_post_generated', 'created_at', 'updated_at', 'generate_post_button')
    actions = ['generate_post_now']
    inlines = [BlogPostInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active', 'generate_post_button')
        }),
        ('Content Generation Settings', {
            'fields': ('tone_of_voice', 'gpt_prompt', 'post_interval_days', 'post_time'),
            'description': 'The tone of voice will be used along with the GPT prompt to generate content in a consistent style.'
        }),
        ('Timestamps', {
            'fields': ('last_post_generated', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:client_id>/generate/',
                self.admin_site.admin_view(self.generate_post_view),
                name='client-generate-post',
            ),
        ]
        return custom_urls + urls

    def generate_post_button(self, obj):
        if obj.id:
            url = reverse('admin:client-generate-post', args=[obj.id])
            return format_html(
                '<a class="button" href="{}">Generate Blog Post Now</a>',
                url
            )
        return ""
    generate_post_button.short_description = "Generate Post"
    generate_post_button.allow_tags = True

    def generate_post_view(self, request, client_id):
        if not request.user.is_staff:
            raise PermissionDenied
        
        try:
            client = Client.objects.get(id=client_id)
            if not client.is_active:
                messages.error(request, f"Cannot generate post for inactive client: {client.name}")
            else:
                # Run the task synchronously
                generate_blog_posts(client_id)
                messages.success(request, f"Blog post generated successfully for {client.name}")
        except Client.DoesNotExist:
            messages.error(request, "Client not found")
        except Exception as e:
            messages.error(request, f"Error generating post: {str(e)}")
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:blogs_client_changelist')))

    def view_posts(self, obj):
        url = reverse('admin:blogs_blogpost_changelist')
        return format_html('<a href="{}?client__id__exact={}">View All Posts</a>', url, obj.id)
    view_posts.short_description = "Blog Posts"

    def generate_post_now(self, request, queryset):
        for client in queryset:
            if not client.is_active:
                messages.error(request, f"Cannot generate post for inactive client: {client.name}")
                continue
            
            try:
                generate_blog_posts(client.id)
                messages.success(request, f"Blog post generated successfully for {client.name}")
            except Exception as e:
                messages.error(request, f"Error generating post for {client.name}: {str(e)}")
    
    generate_post_now.short_description = "Generate blog post now"

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
