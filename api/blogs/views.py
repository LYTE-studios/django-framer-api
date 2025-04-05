from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.conf import settings
import stripe
import secrets
from .models import Client, BlogPost, Subscription
from .serializers import (
    ClientSerializer, 
    BlogPostSerializer, 
    UserSerializer, 
    SubscriptionSerializer,
    RegisterSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create client profile
            client = Client.objects.create(
                user=user,
                name=request.data.get('company_name', user.email),
                embed_token=secrets.token_urlsafe(32)
            )
            return Response({
                'user': UserSerializer(user).data,
                'client': ClientSerializer(client).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        user = authenticate(
            username=request.data.get('email'),
            password=request.data.get('password')
        )
        if user:
            login(request, user)
            return Response({
                'user': UserSerializer(user).data,
                'client': ClientSerializer(user.client).data if hasattr(user, 'client') else None
            })
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        try:
            # Create Stripe customer if not exists
            if not request.user.subscription.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    source=request.data.get('token')
                )
                request.user.subscription.stripe_customer_id = customer.id
                request.user.subscription.save()

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=request.user.subscription.stripe_customer_id,
                items=[{'price': request.data.get('price_id')}],
                trial_from_plan=True
            )

            # Update subscription in database
            request.user.subscription.stripe_subscription_id = subscription.id
            request.user.subscription.status = subscription.status
            request.user.subscription.current_period_end = timezone.datetime.fromtimestamp(
                subscription.current_period_end
            )
            request.user.subscription.save()

            return Response(SubscriptionSerializer(request.user.subscription).data)
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def cancel_subscription(self, request):
        try:
            subscription = request.user.subscription
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'canceled'
                subscription.save()
            return Response(SubscriptionSerializer(subscription).data)
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def generate_post(self, request, pk=None):
        client = self.get_object()
        if not client.is_active:
            return Response(
                {"error": "Client is not active"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not client.can_access_blogs():
            return Response(
                {"error": "Active subscription required"},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        try:
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

    @action(detail=True, methods=['post'])
    def regenerate_embed_token(self, request, pk=None):
        client = self.get_object()
        client.embed_token = secrets.token_urlsafe(32)
        client.save()
        return Response({'embed_token': client.embed_token})

class BlogPostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    filterset_fields = ['client', 'status']
    ordering_fields = ['created_at', 'published_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return BlogPost.objects.filter(client__user=self.request.user)

@permission_classes([AllowAny])
class ClientPostsView(generics.ListAPIView):
    """
    Get all published blog posts for a specific client.
    Requires valid embed token.
    """
    serializer_class = BlogPostSerializer

    def get_queryset(self):
        client = get_object_or_404(
            Client, 
            embed_token=self.request.query_params.get('embed_token')
        )
        
        if not client.can_access_blogs():
            return BlogPost.objects.none()
            
        return BlogPost.objects.filter(
            client=client,
            status='published'
        ).order_by('-published_at')

@api_view(['GET'])
@permission_classes([AllowAny])
def get_embed_code(request, client_id):
    """Get the embed code for a client's blog posts"""
    client = get_object_or_404(Client, id=client_id)
    if not client.embed_token:
        client.embed_token = secrets.token_urlsafe(32)
        client.save()
    
    embed_code = f"""
    <div id="blog-embed" data-token="{client.embed_token}"></div>
    <script src="{settings.EMBED_SCRIPT_URL}"></script>
    """
    
    return Response({'embed_code': embed_code})
