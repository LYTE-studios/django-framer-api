from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Client, BlogPost, Subscription, ToneOfVoice

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    company_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'company_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already registered."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'status', 'plan', 'trial_end', 
            'current_period_end', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'status', 'trial_end', 
            'current_period_end', 'created_at', 'updated_at'
        ]

class ToneOfVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToneOfVoice
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']

class ClientSerializer(serializers.ModelSerializer):
    subscription_status = serializers.SerializerMethodField()
    tone_of_voice = ToneOfVoiceSerializer(read_only=True)
    embed_code = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'tone_of_voice', 'gpt_prompt',
            'post_interval_days', 'post_time', 'is_active',
            'last_post_generated', 'created_at', 'embed_token',
            'subscription_status', 'embed_code'
        ]
        read_only_fields = [
            'last_post_generated', 'created_at', 
            'embed_token', 'subscription_status'
        ]
        extra_kwargs = {
            'embed_token': {'write_only': True}
        }

    def get_subscription_status(self, obj):
        if obj.user and hasattr(obj.user, 'subscription'):
            return {
                'status': obj.user.subscription.status,
                'plan': obj.user.subscription.plan,
                'trial_end': obj.user.subscription.trial_end,
                'current_period_end': obj.user.subscription.current_period_end
            }
        return None

    def get_embed_code(self, obj):
        if obj.embed_token:
            return f"""
            <div id="blog-embed" data-token="{obj.embed_token}"></div>
            <script src="{self.context['request'].build_absolute_uri('/static/embed/blog-embed.js')}"></script>
            """
        return None

class BlogPostSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    subjects = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'client', 'client_name', 'title', 
            'content', 'thumbnail', 'status', 'created_at', 
            'published_at', 'ai_score', 'subjects'
        ]
        read_only_fields = [
            'created_at', 'published_at', 
            'ai_score', 'subjects'
        ]