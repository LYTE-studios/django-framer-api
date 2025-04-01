from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse, path
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from .models import Client, BlogPost, ToneOfVoice, ToneOfVoiceExample, BlogSubject, SpecialEvent
from .tasks import generate_blog_posts
import logging

logger = logging.getLogger(__name__)


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
    change_list_template = 'admin/blogs/client_changelist.html'
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
        urls = super(ClientAdmin, self).get_urls()
        custom_urls = [
            path(
                '<int:client_id>/generate/',
                self.admin_site.admin_view(self.generate_post_view),
                name='client-generate-post',
            ),
            path(
                'upcoming-posts/',
                self.admin_site.admin_view(self.upcoming_posts_view),
                name='upcoming-posts',
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
                task = generate_blog_posts.delay(client_id)
                request.session[f'blog_generation_task_{client_id}'] = task.id
                messages.info(request, f"Blog post generation started for {client.name}. This may take a few minutes.")
                
        except Client.DoesNotExist:
            messages.error(request, "Client not found")
        except Exception as e:
            messages.error(request, f"Error starting blog generation: {str(e)}")
            logger.exception("Error in generate_post_view")
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('admin:blogs_client_changelist')))

    def upcoming_posts_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        
        now = timezone.localtime(timezone.now())
        active_clients = Client.objects.filter(is_active=True)
        
        upcoming_posts = []
        for client in active_clients:
            next_post = client.get_next_post_datetime()
            if next_post <= now + timezone.timedelta(hours=48):
                upcoming_posts.append({
                    'client': client,
                    'scheduled_time': next_post,
                    'time_until': next_post - now,
                })
        
        upcoming_posts.sort(key=lambda x: x['scheduled_time'])
        
        context = {
            'title': 'Upcoming Blog Posts',
            'upcoming_posts': upcoming_posts,
            'now': now,
            **self.admin_site.each_context(request),
        }
        
        return TemplateResponse(request, 'admin/blogs/upcoming_posts.html', context)

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
    list_display = ('title', 'client', 'status', 'created_at', 'published_at', 'ai_score', 'get_subjects')
    list_filter = ('status', 'client', 'created_at', 'related_event')
    search_fields = ('title', 'content', 'client__name', 'subjects__name')
    readonly_fields = ('created_at', 'published_at', 'ai_score')
    actions = ['recheck_ai_scores']
    
    fieldsets = (
        (None, {
            'fields': ('client', 'title', 'content')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Topics and Events', {
            'fields': ('subjects', 'related_event'),
            'description': 'Associated subjects and special events'
        }),
        ('AI Detection', {
            'fields': ('ai_score',),
            'description': 'AI detection score (0-100, lower is more human-like)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'published_at'),
            'classes': ('collapse',)
        })
    )

    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    get_subjects.short_description = "Subjects"


@admin.register(BlogSubject)
class BlogSubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'client', 'usage_count', 'last_used')
    list_filter = ('client',)
    search_fields = ('name', 'client__name')
    readonly_fields = ('usage_count', 'last_used')


@admin.register(SpecialEvent)
class SpecialEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'importance_level')
    list_filter = ('importance_level', 'date')
    search_fields = ('name', 'description')
    ordering = ('date',)
