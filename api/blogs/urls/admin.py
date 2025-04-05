from django.urls import path
from ..views import (
    AdminDashboardView,
    AdminClientListView,
    AdminSubscriptionListView,
    AdminBlogPostListView,
    AdminAnalyticsView,
    AdminSettingsView,
)

app_name = 'admin_portal'

urlpatterns = [
    # Admin Dashboard
    path('', AdminDashboardView.as_view(), name='dashboard'),
    
    # Client Management
    path('clients/', AdminClientListView.as_view(), name='clients'),
    path('clients/<int:pk>/', AdminClientListView.as_view(), name='client-detail'),
    path('clients/<int:pk>/posts/', AdminClientListView.as_view(), name='client-posts'),
    
    # Subscription Management
    path('subscriptions/', AdminSubscriptionListView.as_view(), name='subscriptions'),
    path('subscriptions/<int:pk>/', AdminSubscriptionListView.as_view(), name='subscription-detail'),
    
    # Blog Posts Management
    path('posts/', AdminBlogPostListView.as_view(), name='posts'),
    path('posts/<int:pk>/', AdminBlogPostListView.as_view(), name='post-detail'),
    path('posts/upcoming/', AdminBlogPostListView.as_view(), name='upcoming-posts'),
    
    # Analytics
    path('analytics/', AdminAnalyticsView.as_view(), name='analytics'),
    path('analytics/posts/', AdminAnalyticsView.as_view(), name='post-analytics'),
    path('analytics/clients/', AdminAnalyticsView.as_view(), name='client-analytics'),
    path('analytics/subscriptions/', AdminAnalyticsView.as_view(), name='subscription-analytics'),
    
    # Settings
    path('settings/', AdminSettingsView.as_view(), name='settings'),
    path('settings/general/', AdminSettingsView.as_view(), name='general-settings'),
    path('settings/stripe/', AdminSettingsView.as_view(), name='stripe-settings'),
    path('settings/email/', AdminSettingsView.as_view(), name='email-settings'),
]