from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from ..models import Client, BlogPost, Subscription

class ClientRequiredMixin(LoginRequiredMixin):
    """Verify that the current user has an associated client and active subscription"""
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated (from LoginRequiredMixin)
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Redirect to settings if user has no active subscription
        if hasattr(request.user, 'subscription') and not request.user.subscription.is_active():
            return redirect('client:settings')
        
        # Create a client if one doesn't exist
        if not hasattr(request.user, 'client'):
            Client.objects.create(
                user=request.user,
                name=f"{request.user.email}'s Blog"  # Default name
            )
            
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

class ClientDashboardView(ClientRequiredMixin, TemplateView):
    template_name = 'client/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.request.user.client
        user = self.request.user
        
        # Get recent posts
        context['recent_posts'] = BlogPost.objects.filter(
            client=client
        ).order_by('-created_at')[:5]
        
        # Check for incomplete profile items
        incomplete_items = []
        if not client.name:
            incomplete_items.append(('Set your business name', 'client:settings'))
        if not client.tone_of_voice:
            incomplete_items.append(('Choose your tone of voice', 'client:settings'))
        if not client.gpt_prompt:
            incomplete_items.append(('Define your content requirements', 'client:settings'))
        if not user.first_name or not user.last_name:
            incomplete_items.append(('Complete your personal profile', 'client:profile'))
            
        context['incomplete_items'] = incomplete_items
        context['total_posts'] = BlogPost.objects.filter(client=client).count()
        
        return context

class ClientBlogPostsView(ClientRequiredMixin, ListView):
    template_name = 'client/posts.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            client=self.request.user.client
        ).order_by('-created_at')

from django.conf import settings

class ClientSettingsView(ClientRequiredMixin, UpdateView):
    template_name = 'client/settings.html'
    model = Client
    fields = ['name', 'tone_of_voice', 'gpt_prompt', 'post_interval_days', 'post_time']
    success_url = reverse_lazy('client:settings')
    
    def get_object(self):
        return self.request.user.client
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'subscription'):
            context['subscription'] = self.request.user.subscription
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context

class ClientProfileView(ClientRequiredMixin, UpdateView):
    template_name = 'client/profile.html'
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('client:profile')
    
    def get_object(self):
        return self.request.user

class ClientTestView(ClientRequiredMixin, TemplateView):
    template_name = 'client/test.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the embed code from settings view
        with open('blogs/templates/embed/blog-embed.js', 'r') as f:
            embed_code = f.read()
        context['embed_code'] = f'<script>{embed_code}</script>'
        return context

class ClientSubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'client/subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'subscription'):
            context['subscription'] = self.request.user.subscription
        if hasattr(self.request.user, 'client'):
            context['client'] = self.request.user.client
        return context