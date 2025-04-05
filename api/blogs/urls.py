from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    ClientViewSet, 
    BlogPostViewSet, 
    ClientPostsView,
    AuthViewSet,
    SubscriptionViewSet,
    get_embed_code
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'subscription', SubscriptionViewSet, basename='subscription')
router.register(r'clients', ClientViewSet)
router.register(r'posts', BlogPostViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints are handled by the router:
    # POST /api/blogs/auth/register/
    # POST /api/blogs/auth/login/
    
    # Subscription endpoints are handled by the router:
    # POST /api/blogs/subscription/create_subscription/
    # POST /api/blogs/subscription/cancel_subscription/
    
    # Client posts with embed token
    path('posts/', ClientPostsView.as_view(), name='client-posts'),
    
    # Get embed code
    path('clients/<int:client_id>/embed-code/', get_embed_code, name='get-embed-code'),
]