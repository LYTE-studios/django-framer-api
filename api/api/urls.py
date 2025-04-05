"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from blogs.views.auth import RegisterView

urlpatterns = [
    # Redirect root to client portal
    path('', RedirectView.as_view(url='/client/', permanent=True)),

    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='client/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/client/'), name='logout'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    
    # Password Reset URLs
    path('accounts/password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='client/password_reset_form.html',
             email_template_name='client/password_reset_email.html',
             subject_template_name='client/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('accounts/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='client/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='client/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='client/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('client/', include('blogs.urls.client')),
    path('api/', include('blogs.urls.api')),
    
    # Django admin
    path('api/admin/', admin.site.urls),
]
