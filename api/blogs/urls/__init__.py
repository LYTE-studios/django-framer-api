"""
URL configuration for the blogs app.
This module provides URL patterns for the client portal, API, and admin interfaces.
"""

from django.urls import path, include

app_name = 'blogs'

urlpatterns = [
    # Include URL patterns from each section
    path('', include('blogs.urls.client', namespace='client')),
    path('', include('blogs.urls.api', namespace='api')),
    path('', include('blogs.urls.admin', namespace='admin_portal')),
]