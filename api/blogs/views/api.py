from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
from ..models import BlogPost, Client, Subscription
from ..serializers import (
    BlogPostSerializer,
    ClientSerializer,
    SubscriptionSerializer,
    UserSerializer
)

class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing blog posts.
    """
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return BlogPost.objects.all()
        return BlogPost.objects.filter(client=self.request.user.client)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user.client)

class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for authentication-related operations.
    """
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        """Login endpoint"""
        from django.contrib.auth import authenticate, login
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            })
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Logout endpoint"""
        from django.contrib.auth import logout
        
        logout(request)
        return Response({'message': 'Logged out successfully'})

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ClientPostsView(APIView):
    """
    View for public blog posts access with embed token.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        embed_token = request.GET.get('token')
        if not embed_token:
            return Response({
                'error': 'Embed token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        client = get_object_or_404(Client, embed_token=embed_token)
        posts = BlogPost.objects.filter(
            client=client,
            status='published'
        ).order_by('-published_at')

        serializer = BlogPostSerializer(posts, many=True)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_embed_code(request, client_id):
    """
    Generate embed code for a client's blog posts.
    """
    client = get_object_or_404(Client, id=client_id)
    
    # Ensure user has permission to access this client
    if not request.user.is_staff and request.user.client != client:
        return Response({
            'error': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)

    # Generate or return existing embed token
    if not client.embed_token:
        client.generate_embed_token()
        client.save()

    embed_code = f"""
    <div id="lyte-blog-posts"></div>
    <script src="{settings.FRONTEND_URL}/embed/blog-embed.js"></script>
    <script>
        initLyteBlog('{client.embed_token}');
    </script>
    """

    return Response({
        'embed_code': embed_code,
        'token': client.embed_token
    })