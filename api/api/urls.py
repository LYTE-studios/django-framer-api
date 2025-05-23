"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Client portal URLs
    path('', include('blogs.urls.client', namespace='client')),
    path('client/', RedirectView.as_view(url='/', permanent=True)),
    
    # API URLs
    path('api/', include('blogs.urls.api')),
    
    # Django admin
    path('api/admin/', admin.site.urls),
]
