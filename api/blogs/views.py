from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Client, BlogPost
from .serializers import ClientSerializer, BlogPostSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    @action(detail=True, methods=['post'])
    def generate_post(self, request, pk=None):
        client = self.get_object()
        if not client.is_active:
            return Response(
                {"error": "Client is not active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # This will be implemented in the Celery task
        try:
            # Placeholder for the actual blog generation task
            blog_post = BlogPost.objects.create(
                client=client,
                title="Placeholder Title",
                content="Content will be generated",
                status='draft'
            )
            client.last_post_generated = timezone.now()
            client.save()
            
            return Response(
                BlogPostSerializer(blog_post).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    filterset_fields = ['client', 'status']
    ordering_fields = ['created_at', 'published_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client_id', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset


@permission_classes([AllowAny])
class ClientPostsView(generics.ListAPIView):
    """
    Get all published blog posts for a specific client.
    No authentication required.
    """
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        client = get_object_or_404(Client, pk=self.kwargs['client_id'])
        return BlogPost.objects.filter(
            client=client,
            status='published'
        ).order_by('-published_at')
