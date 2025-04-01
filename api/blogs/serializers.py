from rest_framework import serializers
from .models import Client, BlogPost

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'post_interval_days', 'post_time', 'is_active', 'last_post_generated', 'created_at']
        read_only_fields = ['last_post_generated', 'created_at']

class BlogPostSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)

    class Meta:
        model = BlogPost
        fields = ['id', 'client', 'client_name', 'title', 'content', 'status', 'created_at', 'published_at', 'ai_score']
        read_only_fields = ['created_at', 'published_at', 'ai_score']