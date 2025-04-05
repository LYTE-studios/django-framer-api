"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect root to client portal
    path('', RedirectView.as_view(url='/client/', permanent=True)),
    
    # Client portal routes
    path('client/', include('blogs.urls.client')),
    
    # API routes
    path('api/', include('blogs.urls.api')),
    
    # Admin routes (both Django admin and custom admin)
    path('api/admin/', admin.site.urls),
    path('api/admin/portal/', include('blogs.urls.admin')),
    
    # Authentication routes
    path('api/auth/', include('rest_framework.urls')),
]
