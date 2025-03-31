import os
import openai
from celery import shared_task
from django.utils import timezone
from .models import Client, BlogPost

@shared_task
def generate_blog_posts():
    clients = Client.objects.filter(is_active=True)
    for client in clients:
        if client.is_due_for_post():
            try:
                # Initialize OpenAI client
                openai.api_key = os.getenv('OPENAI_API_KEY')
                
                # Generate blog post using ChatGPT
                completion = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": client.gpt_prompt},
                        {"role": "user", "content": "Generate a blog post"}
                    ]
                )
                
                # Extract content from response
                content = completion.choices[0].message.content
                
                # Create blog post
                blog_post = BlogPost.objects.create(
                    client=client,
                    title=content.split('\n')[0],  # First line as title
                    content=content,
                    status='published',
                    published_at=timezone.now()
                )
                
                # Update client's last post time
                client.last_post_generated = timezone.now()
                client.save()
                
            except Exception as e:
                BlogPost.objects.create(
                    client=client,
                    title="Error Generating Post",
                    content="",
                    status='error',
                    error_message=str(e)
                )

@shared_task
def retry_failed_posts():
    failed_posts = BlogPost.objects.filter(status='error')
    for post in failed_posts:
        try:
            generate_blog_posts.delay()
        except Exception:
            continue