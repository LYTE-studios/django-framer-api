from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch
from .models import Client, BlogPost

class ClientModelTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Test Client",
            gpt_prompt="Write in a professional tone",
            post_interval_hours=24
        )

    def test_client_creation(self):
        self.assertEqual(self.client_obj.name, "Test Client")
        self.assertEqual(self.client_obj.post_interval_hours, 24)
        self.assertTrue(self.client_obj.is_active)

    def test_is_due_for_post(self):
        # Should be due when no posts exist
        self.assertTrue(self.client_obj.is_due_for_post())

        # Set last post to now
        self.client_obj.last_post_generated = timezone.now()
        self.client_obj.save()
        self.assertFalse(self.client_obj.is_due_for_post())

        # Set last post to 25 hours ago
        self.client_obj.last_post_generated = timezone.now() - timezone.timedelta(hours=25)
        self.client_obj.save()
        self.assertTrue(self.client_obj.is_due_for_post())

class BlogPostModelTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Test Client",
            gpt_prompt="Write in a professional tone"
        )
        self.post = BlogPost.objects.create(
            client=self.client_obj,
            title="Test Post",
            content="Test Content",
            status="draft"
        )

    def test_blog_post_creation(self):
        self.assertEqual(self.post.title, "Test Post")
        self.assertEqual(self.post.status, "draft")
        self.assertIsNone(self.post.published_at)

class APITests(APITestCase):
    def setUp(self):
        # Create test user and get token
        self.user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create test client
        self.test_client = Client.objects.create(
            name="API Test Client",
            gpt_prompt="Write in a professional tone",
            post_interval_hours=24
        )

    def test_list_clients(self):
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "API Test Client")

    def test_create_client(self):
        data = {
            'name': 'New Client',
            'gpt_prompt': 'Write in a casual tone',
            'post_interval_hours': 12
        }
        response = self.client.post('/api/clients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 2)

    def test_generate_post_endpoint(self):
        with patch('blogs.tasks.generate_blog_posts.delay') as mock_task:
            response = self.client.post(f'/api/clients/{self.test_client.id}/generate_post/')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['status'], 'draft')

    def test_unauthorized_access(self):
        # Remove credentials
        self.client.credentials()
        response = self.client.get('/api/clients/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class TaskTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name="Test Client",
            gpt_prompt="Write in a professional tone",
            post_interval_hours=24
        )

    @patch('openai.ChatCompletion.create')
    def test_generate_blog_posts(self, mock_openai):
        # Mock OpenAI response
        mock_openai.return_value.choices[0].message.content = "Test Title\n\nTest Content"
        
        from .tasks import generate_blog_posts
        generate_blog_posts()

        # Check if blog post was created
        post = BlogPost.objects.first()
        self.assertIsNotNone(post)
        self.assertEqual(post.title, "Test Title")
        self.assertEqual(post.status, "published")

    def test_retry_failed_posts(self):
        # Create a failed post
        BlogPost.objects.create(
            client=self.client_obj,
            title="Failed Post",
            content="",
            status="error",
            error_message="Test error"
        )

        from .tasks import retry_failed_posts
        with patch('blogs.tasks.generate_blog_posts.delay') as mock_task:
            retry_failed_posts()
            mock_task.assert_called_once()
