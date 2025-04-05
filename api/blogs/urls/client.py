from django.urls import path
from django.views.generic import TemplateView
from ..views import (
    ClientDashboardView,
    ClientSettingsView,
    ClientSubscriptionView,
    ClientBlogPostsView,
    ClientProfileView,
)

app_name = 'client'

urlpatterns = [
    # Client Dashboard
    path('', ClientDashboardView.as_view(), name='dashboard'),
    
    # Blog Posts Management
    path('posts/', ClientBlogPostsView.as_view(), name='posts'),
    path('posts/new/', ClientBlogPostsView.as_view(), name='new-post'),
    path('posts/<int:pk>/', ClientBlogPostsView.as_view(), name='edit-post'),
    
    # Settings and Configuration
    path('settings/', ClientSettingsView.as_view(), name='settings'),
    path('settings/profile/', ClientProfileView.as_view(), name='profile'),
    path('settings/embed/', TemplateView.as_view(
        template_name='client/embed_instructions.html'
    ), name='embed'),
    
    # Subscription Management
    path('subscription/', ClientSubscriptionView.as_view(), name='subscription'),
    path('subscription/plans/', ClientSubscriptionView.as_view(), name='plans'),
    path('subscription/billing/', ClientSubscriptionView.as_view(), name='billing'),
    path('subscription/invoices/', ClientSubscriptionView.as_view(), name='invoices'),
]