from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse, resolve
from django.shortcuts import redirect, resolve_url
from django.utils import timezone
from django.contrib import messages
import stripe
from ..models import Client, BlogPost, Subscription

class OnboardingRequiredMixin(LoginRequiredMixin):
    """Verify that the user has completed onboarding"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Create a client if one doesn't exist
        if not hasattr(request.user, 'client'):
            Client.objects.create(
                user=request.user,
                name=f"{request.user.email}'s Blog"  # Default name
            )
        
        # Check if onboarding is completed
        onboarding_url = resolve_url('client:onboarding')
        if not request.user.client.completed_onboarding and request.path != onboarding_url:
            return redirect('client:onboarding')
            
        # Check subscription status
        if hasattr(request.user, 'subscription') and not request.user.subscription.is_active():
            return redirect('client:settings')
            
        return super().dispatch(request, *args, **kwargs)

class ClientRequiredMixin(OnboardingRequiredMixin):
    """Legacy mixin name for backward compatibility"""
    pass

class OnboardingView(LoginRequiredMixin, UpdateView):  # Intentionally not using OnboardingRequiredMixin
    template_name = 'client/onboarding.html'
    model = Client
    fields = ['name']
    success_url = reverse_lazy('client:dashboard')
    
    def get_object(self):
        # Get or create client for the current user
        client, created = Client.objects.get_or_create(
            user=self.request.user,
            defaults={'name': f"{self.request.user.email}'s Blog"}
        )
        return client
    
    def form_valid(self, form):
        client = form.save(commit=False)
        # Use the description to create a GPT prompt
        description = self.request.POST.get('description', '')
        industry = self.request.POST.get('industry', '')
        client.gpt_prompt = f"""Industry: {industry}
Business Description: {description}

Generate blog posts that:
1. Are relevant to our industry and business focus
2. Provide value to our target audience
3. Showcase our expertise and knowledge
4. Use a professional and engaging tone
"""
        client.completed_onboarding = True
        client.save()
        return super().form_valid(form)

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
    fields = [
        'name', 'tone_of_voice', 'gpt_prompt', 'post_interval_days', 'post_time',
        'company_name', 'vat_number', 'billing_address_line1', 'billing_address_line2',
        'billing_city', 'billing_state', 'billing_postal_code', 'billing_country'
    ]
    success_url = reverse_lazy('client:settings')
    
    def get_object(self):
        return self.request.user.client
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'subscription'):
            context['subscription'] = self.request.user.subscription
            # Get invoices from Stripe if subscription exists
            if self.request.user.subscription.stripe_customer_id:
                try:
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    invoices = stripe.Invoice.list(
                        customer=self.request.user.subscription.stripe_customer_id,
                        limit=10,
                        status='paid'  # Only get paid invoices
                    )
                    context['invoices'] = [{
                        'number': invoice.number,
                        'amount': f"€{invoice.total / 100:.2f}",
                        'date': timezone.datetime.fromtimestamp(invoice.created),
                        'url': invoice.invoice_pdf,
                        'status': invoice.status
                    } for invoice in invoices.data]
                except stripe.error.StripeError as e:
                    messages.error(self.request, "Unable to fetch invoices. Please try again later.")
                    context['invoices'] = []
        
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        return context

    def form_valid(self, form):
        """Update Stripe customer billing details when billing info is updated"""
        response = super().form_valid(form)
        if hasattr(self.request.user, 'subscription') and self.request.user.subscription.stripe_customer_id:
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                stripe.Customer.modify(
                    self.request.user.subscription.stripe_customer_id,
                    name=form.cleaned_data['company_name'],
                    tax_id_data=[{'type': 'eu_vat', 'value': form.cleaned_data['vat_number']}] if form.cleaned_data['vat_number'] else None,
                    address={
                        'line1': form.cleaned_data['billing_address_line1'],
                        'line2': form.cleaned_data['billing_address_line2'],
                        'city': form.cleaned_data['billing_city'],
                        'state': form.cleaned_data['billing_state'],
                        'postal_code': form.cleaned_data['billing_postal_code'],
                        'country': form.cleaned_data['billing_country'],
                    }
                )
                messages.success(self.request, "Settings and billing information updated successfully.")
            except stripe.error.StripeError as e:
                messages.warning(self.request, "Settings saved but unable to update billing information. Please try again later.")
        return response

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

class ClientSubscriptionView(OnboardingRequiredMixin, TemplateView):
    template_name = 'client/subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'subscription'):
            context['subscription'] = self.request.user.subscription
        if hasattr(self.request.user, 'client'):
            context['client'] = self.request.user.client
        return context