"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Redirect root to client portal
    path('', include('blogs.urls.client')),
        
    path('api/', include('blogs.urls.api')),
    
    # Django admin
    path('api/admin/', admin.site.urls),
]
