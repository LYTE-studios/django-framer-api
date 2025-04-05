from django.urls import path

from blogs.views.client import *
from blogs.views.auth import *
from blogs.forms import EmailAuthenticationForm
from django.contrib.auth import views as auth_views

urlpatterns = [
# Blog Posts
    path ('', ClientDashboardView.as_view(), name='dashboard'),
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

    path('delete-account/', ClientProfileView.as_view(), name='delete_account'),

    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='client/login.html',
        authentication_form=EmailAuthenticationForm
    ), name='login'),
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
]
    


    