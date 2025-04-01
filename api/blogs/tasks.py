from openai import OpenAI
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Client, BlogPost
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@shared_task
def generate_blog_posts(client_id=None):
    # Get API key from environment first, then settings
    api_key = os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY
    if not api_key:
        logger.error("No OpenAI API key found")
        raise ValueError("OpenAI API key not configured")

    logger.info(f"Using API key ending in ...{api_key[-4:]}")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    if client_id:
        # Generate for specific client
        try:
            client_obj = Client.objects.get(id=client_id)
            if not client_obj.is_active:
                return
            
            # Prepare the system message with tone of voice examples
            system_message = client_obj.gpt_prompt + "\n\n"
            if client_obj.tone_of_voice:
                system_message += client_obj.tone_of_voice.get_formatted_examples()
            system_message += "\nPlease generate a blog post that matches this tone of voice while addressing the client's specific needs."

            # Generate blog post using ChatGPT
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": "Generate a blog post"}
                ]
            )
            
            # Extract content from response
            full_content = completion.choices[0].message.content
            title = full_content.split('\n')[0].replace('Title: ', '')  # First line as title, remove "Title: " if present
            content = '\n'.join(full_content.split('\n')[1:]).strip()  # Rest of the content
            
            # Create blog post
            blog_post = BlogPost.objects.create(
                client=client_obj,
                title=title,
                content=content,
                status='published',
                published_at=timezone.now()
            )
            
            # Update client's last post time
            client_obj.last_post_generated = timezone.now()
            client_obj.save()
            
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            BlogPost.objects.create(
                client=client_obj,
                title="Error Generating Post",
                content="",
                status='error',
                error_message=str(e)
            )
    else:
        # Generate for all due clients
        clients = Client.objects.filter(is_active=True)
        for client_obj in clients:
            if client_obj.is_due_for_post():
                try:
                    # Prepare the system message with tone of voice examples
                    system_message = client_obj.gpt_prompt + "\n\n"
                    if client_obj.tone_of_voice:
                        system_message += client_obj.tone_of_voice.get_formatted_examples()
                    system_message += "\nPlease generate a blog post that matches this tone of voice while addressing the client's specific needs."

                    # Generate blog post using ChatGPT
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": "Generate a blog post"}
                        ]
                    )
                    
                    # Extract content from response
                    full_content = completion.choices[0].message.content
                    title = full_content.split('\n')[0].replace('Title: ', '')  # First line as title, remove "Title: " if present
                    content = '\n'.join(full_content.split('\n')[1:]).strip()  # Rest of the content
                    
                    # Create blog post
                    blog_post = BlogPost.objects.create(
                        client=client_obj,
                        title=title,
                        content=content,
                        status='published',
                        published_at=timezone.now()
                    )
                    
                    # Update client's last post time
                    client_obj.last_post_generated = timezone.now()
                    client_obj.save()
                    
                except Exception as e:
                    logger.error(f"Error generating post: {str(e)}")
                    BlogPost.objects.create(
                        client=client_obj,
                        title="Error Generating Post",
                        content="",
                        status='error',
                        error_message=str(e)
                    )

@shared_task
def retry_failed_posts():
    # Get API key from environment first, then settings
    api_key = os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY
    if not api_key:
        logger.error("No OpenAI API key found")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Get the latest failed post for each client
    failed_posts = BlogPost.objects.filter(
        status='error'
    ).order_by('client_id', '-created_at').distinct('client_id')
    
    for post in failed_posts:
        client_obj = post.client
        if client_obj.is_due_for_post():
            try:
                # Prepare the system message with tone of voice examples
                system_message = client_obj.gpt_prompt + "\n\n"
                if client_obj.tone_of_voice:
                    system_message += client_obj.tone_of_voice.get_formatted_examples()
                system_message += "\nPlease generate a blog post that matches this tone of voice while addressing the client's specific needs."

                # Generate blog post using ChatGPT
                completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": "Generate a blog post"}
                    ]
                )
                
                # Extract content from response
                full_content = completion.choices[0].message.content
                title = full_content.split('\n')[0].replace('Title: ', '')  # First line as title, remove "Title: " if present
                content = '\n'.join(full_content.split('\n')[1:]).strip()  # Rest of the content
                
                # Update the failed post
                post.title = title
                post.content = content
                post.status = 'published'
                post.published_at = timezone.now()
                post.error_message = None
                post.save()
                
                # Update client's last post time
                client_obj.last_post_generated = timezone.now()
                client_obj.save()
                
            except Exception as e:
                logger.error(f"Error retrying failed post: {str(e)}")
                continue