from rest_framework.routers import DefaultRouter
from django.urls import path
from ..views import (
    BlogPostViewSet,
    ClientPostsView,
    AuthViewSet,
    SubscriptionViewSet,
    get_embed_code
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'subscription', SubscriptionViewSet, basename='subscription')
router.register(r'posts', BlogPostViewSet, basename='post')

urlpatterns = [
    # Public blog posts endpoint (requires embed token)
    path('posts/', ClientPostsView.as_view(), name='client-posts'),
    
    # Embed code generation
    path('embed-code/<int:client_id>/', get_embed_code, name='get-embed-code'),
    
    # Include router URLs
    *router.urls,
]