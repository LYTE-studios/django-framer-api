from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from ..forms import EmailUserCreationForm
from ..models import Client

class RegisterView(CreateView):
    form_class = EmailUserCreationForm
    template_name = 'client/register.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log in the user after successful registration
        login(self.request, self.object)
        return response
    
    def get_success_url(self):
        return reverse_lazy('client:onboarding')

class OnboardingView(LoginRequiredMixin, UpdateView):
    model = Client
    template_name = 'client/onboarding.html'
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
        client.save()
        return super().form_valid(form)