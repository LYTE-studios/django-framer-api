from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from ..views import (
    ClientDashboardView,
    ClientSettingsView,
    ClientSubscriptionView,
    ClientBlogPostsView,
    ClientProfileView,
)

app_name = 'client'

urlpatterns = [
    # Dashboard
    path('', ClientDashboardView.as_view(), name='dashboard'),
    
    # Blog Posts
    path('posts/', ClientBlogPostsView.as_view(), name='posts'),
    path('posts/new/', ClientBlogPostsView.as_view(), name='new-post'),
    path('posts/<int:pk>/', ClientBlogPostsView.as_view(), name='edit-post'),
    
    # Settings
    path('settings/', ClientSettingsView.as_view(), name='settings'),
    path('settings/profile/', ClientProfileView.as_view(), name='profile'),
    
    # Subscription
    path('subscription/', ClientSubscriptionView.as_view(), name='subscription'),
    path('subscription/create/', ClientSubscriptionView.as_view(), name='create_subscription'),
    path('subscription/cancel/', ClientSubscriptionView.as_view(), name='cancel_subscription'),
    
    # Authentication
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('password-change/', PasswordChangeView.as_view(
        template_name='client/password_change.html',
        success_url='password-change-done'
    ), name='password_change'),
    path('password-change/done/', PasswordChangeDoneView.as_view(
        template_name='client/password_change_done.html'
    ), name='password_change_done'),
    
    # Account Management
    path('delete-account/', ClientProfileView.as_view(), name='delete_account'),
]