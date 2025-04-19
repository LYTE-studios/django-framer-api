from typing import Any, Dict
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse, resolve
from django.shortcuts import redirect, resolve_url
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.contrib import messages
import stripe
import logging
from ..models import Client, BlogPost, Subscription

logger = logging.getLogger(__name__)
class ClientRequiredMixin(LoginRequiredMixin):
    """Verify that the current user has an associated client"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Create a client if one doesn't exist
        if not hasattr(request.user, 'client'):
            Client.objects.create(
                user=request.user,
                name=f"{request.user.email}'s Blog"  # Default name
            )
            
        # Check subscription status
        if hasattr(request.user, 'subscription') and not request.user.subscription.is_active():
            return redirect('client:settings')
            
        return super().dispatch(request, *args, **kwargs)
    pass

from django import forms

from django.views import View
from django.shortcuts import render

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
        # Check for incomplete content settings
        if not client.name:
            incomplete_items.append(('Set your business name', 'client:settings'))
        if not client.industry:
            incomplete_items.append(('Set your company industry', 'client:settings'))
        if not client.business_description:
            incomplete_items.append(('Add your business description', 'client:settings'))
        if not client.content_preferences:
            incomplete_items.append(('Define your content preferences', 'client:settings'))
        

            context['content_settings_incomplete'] = True
            
        context['incomplete_items'] = incomplete_items
        context['total_posts'] = BlogPost.objects.filter(client=client).count()
        context['subscription'] = Subscription.objects.filter(user=user).first()
        context['next_post_datetime'] = self.request.user.client.get_next_post_datetime()
        
        return context

class ClientBlogPostsView(ClientRequiredMixin, ListView):
    template_name = 'client/posts.html'
    context_object_name = 'posts'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        
        context['client'] = self.request.user.client
        context['next_post_datetime'] = self.request.user.client.get_next_post_datetime()

        return context
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            client=self.request.user.client
        ).order_by('-created_at')

from django.conf import settings

class ClientSettingsView(ClientRequiredMixin, UpdateView):
    template_name = 'client/settings.html'
    model = Client
    fields = [
        'name', 'tone_of_voice', 'industry', 'business_description', 'content_preferences', 'post_interval_days', 'post_time',
        'company_name', 'vat_number', 'billing_address_line1', 'billing_address_line2',
        'billing_city', 'billing_state', 'billing_postal_code', 'billing_country'
    ]
    success_url = reverse_lazy('client:settings')
    
    def get_object(self):
        return self.request.user.client
    
    def get_initial(self):
        """Return the initial data to use for forms on this view."""
        initial = super().get_initial()
        client = self.get_object()
        # Add all client fields to initial data
        for field in self.get_form_fields():
            value = getattr(client, field)
            initial[field] = value
            logger.info("Setting initial value for %s: %s", field, value)
        logger.info("Complete initial data: %s", initial)
        return initial

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        form = super().get_form(form_class)
        logger.info("Form initial data: %s", form.initial)
        return form

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

    def post(self, request, *args, **kwargs):
        """Handle POST requests: instantiate a form instance with the passed POST data and then check if it's valid."""
        form_type = request.POST.get('form_type')
        logger.info("Form type: %s", form_type)
        logger.info("POST data: %s", request.POST)
        
        self.object = self.get_object()
        
        if not form_type:
            messages.error(self.request, "Invalid form submission. Please try again.")
            return self.form_invalid(self.get_form())

        # Define fields based on form type
        if form_type == 'content_settings':
            self.fields = ['name', 'industry', 'business_description', 'content_preferences', 'post_interval_days', 'post_time']
            logger.info("Content settings fields: %s", self.fields)
        elif form_type == 'billing_info':
            self.fields = ['company_name', 'vat_number', 'billing_address_line1', 'billing_address_line2',
                          'billing_city', 'billing_state', 'billing_postal_code', 'billing_country']
            logger.info("Billing info fields: %s", self.fields)
        else:
            messages.error(self.request, "Invalid form type. Please try again.")
            return self.form_invalid(self.get_form())

        # Create form with only the needed fields
        form = self.get_form()
        logger.info("Form bound: %s", form.is_bound)
        logger.info("Form data: %s", form.data)
        
        if form.is_valid():
            logger.info("Form is valid")
            logger.info("Cleaned data: %s", form.cleaned_data)
            return self.form_valid(form)
        else:
            logger.error("Form is invalid")
            logger.error("Form errors: %s", form.errors)
            logger.error("Non-field errors: %s", form.non_field_errors())
            return self.form_invalid(form)

    def get_form_class(self):
        """Return the form class to use in this view."""
        from django.forms import modelform_factory
        if not hasattr(self, 'fields'):
            self.fields = self.get_form_fields()
        return modelform_factory(self.model, fields=self.fields)

    def get_form_fields(self):
        """Get the default fields if no specific form type is set."""
        return [
            'name', 'tone_of_voice', 'industry', 'business_description', 'content_preferences',
            'post_interval_days', 'post_time', 'company_name', 'vat_number',
            'billing_address_line1', 'billing_address_line2', 'billing_city',
            'billing_state', 'billing_postal_code', 'billing_country'
        ]

    def form_valid(self, form):
        """Save the form and update Stripe customer if needed"""
        from django.db import transaction
        
        logger.info("Form data before save: %s", form.cleaned_data)
        logger.info("Form fields: %s", list(form.fields.keys()))
        
        try:
            with transaction.atomic():
                # Get current client data
                client = Client.objects.select_for_update().get(id=self.get_object().id)
                
                # Update fields from form
                for field, value in form.cleaned_data.items():
                    if field in form.fields:
                        setattr(client, field, value)
                        logger.info("Setting field %s to value: %s", field, value)
                
                # Save the client
                client.save(force_update=True)
                
                # Verify the save by fetching fresh from DB
                fresh_client = Client.objects.get(id=client.id)
                logger.info("Fresh client data after save: %s", {
                    'id': fresh_client.id,
                    'industry': fresh_client.industry,
                    'business_description': fresh_client.business_description,
                    'content_preferences': fresh_client.content_preferences,
                    'company_name': fresh_client.company_name,
                    'vat_number': fresh_client.vat_number
                })
                
                # Only update Stripe if this is billing info
                stripe_updated = False
                if 'company_name' in form.cleaned_data and hasattr(self.request.user, 'subscription') and self.request.user.subscription.stripe_customer_id:
                    try:
                        stripe.api_key = settings.STRIPE_SECRET_KEY
                        stripe.Customer.modify(
                            self.request.user.subscription.stripe_customer_id,
                            name=form.cleaned_data['company_name'],
                            tax_id_data=[{'type': 'eu_vat', 'value': form.cleaned_data['vat_number']}] if form.cleaned_data.get('vat_number') else None,
                            address={
                                'line1': form.cleaned_data.get('billing_address_line1'),
                                'line2': form.cleaned_data.get('billing_address_line2'),
                                'city': form.cleaned_data.get('billing_city'),
                                'state': form.cleaned_data.get('billing_state'),
                                'postal_code': form.cleaned_data.get('billing_postal_code'),
                                'country': form.cleaned_data.get('billing_country'),
                            }
                        )
                        stripe_updated = True
                    except stripe.error.StripeError as e:
                        logger.error("Error updating Stripe customer: %s", str(e))
                        messages.warning(self.request, "Settings saved but unable to update billing information in Stripe.")
                        return HttpResponseRedirect(self.get_success_url())

                # Show success message
                if stripe_updated:
                    messages.success(self.request, "Settings and billing information updated successfully.")
                else:
                    messages.success(self.request, "Settings saved successfully.")

        except Exception as e:
            logger.error("Error saving form: %s", str(e))
            messages.error(self.request, "Error saving settings. Please try again.")
            return self.form_invalid(form)
        else:
            messages.success(self.request, "Settings updated successfully.")

        return HttpResponseRedirect(self.get_success_url())
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

class ClientSubscriptionView(ClientRequiredMixin, TemplateView):
    template_name = 'client/subscription.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'subscription'):
            context['subscription'] = self.request.user.subscription
        if hasattr(self.request.user, 'client'):
            context['client'] = self.request.user.client
        return context