from openai import OpenAI
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Client, BlogPost
import logging
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@shared_task
def check_ai_score(blog_post_id):
    """
    Check the AI score of a blog post using ZeroGPT API
    Returns a score from 0-100 where lower scores indicate more human-like text
    """
    try:
        blog_post = BlogPost.objects.get(id=blog_post_id)
        
        # ZeroGPT API endpoint
        url = "https://api.zerogpt.com/api/detect/detectText"
        
        # Get API key from environment
        api_key = os.getenv('ZEROGPT_API_KEY')
        if not api_key:
            logger.error("No ZeroGPT API key found")
            return
        
        # Prepare request
        headers = {
            "ApiKey": api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "input_text": blog_post.content
        }
        
        # Create a session with custom SSL settings
        session = requests.Session()
        session.verify = False  # Disable SSL verification
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # Make request to ZeroGPT API
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        logger.info(f"ZeroGPT API Response: {response.text}")
        
        # Extract AI score from response
        result = response.json()

        ai_score = result["data"]["fakePercentage"]
        
        if ai_score is not None:
            # Update blog post with AI score
            blog_post.ai_score = ai_score
            blog_post.save()
            logger.info(f"Updated AI score for blog post {blog_post_id}: {ai_score}")
        else:
            logger.error(f"No AI score returned for blog post {blog_post_id}")
            
    except BlogPost.DoesNotExist:
        logger.error(f"Blog post {blog_post_id} not found")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking AI score for post {blog_post_id}: {str(e)}")
        logger.error(f"Request details - URL: {url}, Headers: {headers}, Data: {data}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response text: {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error checking AI score for post {blog_post_id}")
        logger.exception(e)

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
            
            # Trigger AI score check
            check_ai_score.delay(blog_post.id)
            
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
                    
                    # Trigger AI score check
                    check_ai_score.delay(blog_post.id)
                    
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
                
                # Trigger AI score check
                check_ai_score.delay(post.id)
                
                # Update client's last post time
                client_obj.last_post_generated = timezone.now()
                client_obj.save()
                
            except Exception as e:
                logger.error(f"Error retrying failed post: {str(e)}")
                continue