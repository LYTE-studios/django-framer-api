from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ClientViewSet, BlogPostViewSet, ClientPostsView

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'posts', BlogPostViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('<int:client_id>/posts/', ClientPostsView.as_view(), name='client-posts'),
]