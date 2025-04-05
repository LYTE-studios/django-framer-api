"""
Main URL configuration for the blogs app.
This module provides URL patterns for the client portal, API, and admin interfaces.
"""

from django.urls import path, include

app_name = 'blogs'

urlpatterns = [
    # Client portal routes
    path('client/', include('blogs.urls.client', namespace='client')),
    
    # API routes
    path('', include('blogs.urls.api', namespace='api')),
    
    # Admin portal routes
    path('admin/portal/', include('blogs.urls.admin', namespace='admin_portal')),
]