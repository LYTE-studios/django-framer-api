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

    path('client/', include('blogs.urls.client')),

    path('api/', include('blogs.urls.api')),
    
    # Django admin
    path('api/admin/', admin.site.urls),
]
