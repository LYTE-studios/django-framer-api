from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import BlogPost, Client, Subscription

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'user', 'name', 'tone_of_voice', 'gpt_prompt',
            'post_interval_days', 'post_time', 'embed_token'
        ]
        read_only_fields = ['id', 'embed_token']

class BlogPostSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    subjects = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'client', 'title', 'content', 'status',
            'created_at', 'published_at', 'ai_score', 'subjects',
            'thumbnail'
        ]
        read_only_fields = ['id', 'client', 'created_at', 'ai_score']

    def validate_status(self, value):
        if value == 'published' and not self.instance.published_at:
            from django.utils import timezone
            self.instance.published_at = timezone.now()
        return value

class SubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'status', 'plan', 'stripe_subscription_id',
            'trial_end', 'current_period_end', 'cancel_at_period_end'
        ]
        read_only_fields = [
            'id', 'user', 'stripe_subscription_id',
            'trial_end', 'current_period_end'
        ]

    def validate_plan(self, value):
        """
        Validate plan changes based on subscription status
        """
        if self.instance and self.instance.status != 'active':
            raise serializers.ValidationError(
                "Cannot change plan without an active subscription"
            )
        return value