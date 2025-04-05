from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from ..models import Client, BlogPost, Subscription

class ClientRequiredMixin(LoginRequiredMixin):
    """Verify that the current user has an associated client and active subscription"""
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'client'):
            return redirect('client:subscription')
        if not request.user.subscription.is_active():
            return redirect('client:subscription')
        return super().dispatch(request, *args, **kwargs)

class ClientDashboardView(ClientRequiredMixin, TemplateView):
    template_name = 'client/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_posts'] = BlogPost.objects.filter(
            client=self.request.user.client
        ).order_by('-created_at')[:5]
        return context

class ClientBlogPostsView(ClientRequiredMixin, ListView):
    template_name = 'client/posts.html'
    context_object_name = 'posts'
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            client=self.request.user.client
        ).order_by('-created_at')

class ClientSettingsView(ClientRequiredMixin, UpdateView):
    template_name = 'client/settings.html'
    model = Client
    fields = ['name', 'tone_of_voice', 'gpt_prompt', 'post_interval_days', 'post_time']
    success_url = reverse_lazy('client:settings')
    
    def get_object(self):
        return self.request.user.client

class ClientProfileView(ClientRequiredMixin, UpdateView):
    template_name = 'client/profile.html'
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('client:profile')
    
    def get_object(self):
        return self.request.user

class ClientSubscriptionView(LoginRequiredMixin, TemplateView):
    template_name = 'client/subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'subscription'):
            context['subscription'] = self.request.user.subscription
        return context