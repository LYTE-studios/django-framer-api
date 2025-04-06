from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages

class OnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_url = resolve(request.path).url_name
            onboarding_url = 'client:onboarding'
            
            # Skip check for certain URLs
            skip_urls = [
                'onboarding',
                'logout',
                'login',
                'register',
                'password_reset',
                'password_reset_done',
                'password_reset_confirm',
                'password_reset_complete',
                'static',
                'media'
            ]
            
            # Skip check for onboarding page and static files
            skip_urls = [
                'onboarding',
                'logout',
                'login',
                'register',
                'password_reset',
                'password_reset_done',
                'password_reset_confirm',
                'password_reset_complete',
                'static',
                'media'
            ]
            
            # Don't check onboarding status on onboarding page
            if current_url == 'onboarding':
                return self.get_response(request)
                
            # Skip check for certain URLs
            if current_url not in skip_urls:
                if hasattr(request.user, 'client'):
                    client = request.user.client
                    if not client.completed_onboarding:
                        messages.info(request, "Please complete your onboarding first.")
                        return redirect(onboarding_url)

        response = self.get_response(request)
        return response