from openai import OpenAI
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Client, BlogPost, SpecialEvent, BlogSubject
from django.db.models import Q
from datetime import timedelta
import logging
import os
import requests
from dotenv import load_dotenv
import time

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
        
        # Create a session with proper SSL verification
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # Make request to ZeroGPT API
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        logger.info(f"ZeroGPT API Response: {response.text}")
        
        # Extract AI score from response
        result = response.json()
        
        if "data" in result and "fakePercentage" in result["data"]:
            ai_score = result["data"]["fakePercentage"]
            
            # Validate and normalize the score
            try:
                ai_score = float(ai_score)
                # Ensure score is within 0-100 range
                ai_score = max(0, min(100, ai_score))
                
                # Update blog post with AI score
                blog_post.ai_score = ai_score
                blog_post.save()
                logger.info(f"Updated AI score for blog post {blog_post_id}: {ai_score}")
                
                # If AI score is too high, request a more human-like rewrite
                if ai_score > 25:
                    logger.info(f"AI score {ai_score} is too high, requesting rewrite")
                    
                    # Modify the system message to request a more natural rewrite
                    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY)
                    rewrite_prompt = f"""Please rewrite this blog post to make it more natural and human-like while maintaining professionalism.
                    Current AI detection score: {ai_score}%
                    
                    Original post:
                    Title: {blog_post.title}
                    {blog_post.content}
                    
                    Keep the same core message and information, but rewrite it with:
                    - More natural flow and transitions
                    - Varied sentence structures
                    - Relatable examples or analogies where appropriate
                    - A warm, knowledgeable voice that builds trust
                    
                    Maintain professionalism and credibility while making the content more engaging."""
                    
                    completion = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert content writer who specializes in creating authentic, professional blog content."},
                            {"role": "user", "content": rewrite_prompt}
                        ]
                    )
                    
                    # Extract rewritten content
                    rewritten_content = completion.choices[0].message.content.strip()
                    
                    # Update the blog post
                    blog_post.content = rewritten_content
                    blog_post.save()
                    
                    # Check AI score again
                    check_ai_score(blog_post.id)
            except (ValueError, TypeError):
                logger.error(f"Invalid AI score value received: {ai_score}")
        else:
            logger.error(f"No AI score returned for blog post {blog_post_id}. Response: {result}")
            
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

def get_relevant_event():
    """
    Check for any important events within a 7-day window of the current date
    Returns the most important event if found, otherwise None
    """
    today = timezone.now().date()
    date_range = (today - timedelta(days=3), today + timedelta(days=7))
    
    return SpecialEvent.objects.filter(
        date__range=date_range,
        importance_level__gte=3  # Only consider more important events
    ).order_by('-importance_level', 'date').first()

def extract_subjects(content):
    """
    Extract potential subjects from the blog post content using GPT
    Returns a list of subject strings
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY)
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Extract 2-3 main subjects/topics from this blog post. Respond with only the subjects, one per line."},
            {"role": "user", "content": content}
        ]
    )
    
    subjects = completion.choices[0].message.content.strip().split('\n')
    return [s.strip() for s in subjects if s.strip()]

def get_avoid_subjects(client_obj, lookback_days=90):
    """
    Get subjects to avoid based on recent usage
    Returns a list of subject names
    """
    recent_date = timezone.now() - timedelta(days=lookback_days)
    recent_subjects = BlogSubject.objects.filter(
        client=client_obj,
        last_used__gte=recent_date
    ).order_by('-usage_count')[:10]
    
    return [s.name for s in recent_subjects]

def generate_thumbnail(client_obj, title, content):
    """
    Generate a thumbnail image using DALL-E based on the blog post content
    Returns the URL of the generated image stored in S3
    """
    max_retries = 3
    retry_delay = 2  # seconds

    try:
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY)
        
        # First, generate a description for the image
        prompt = f"""Create a professional blog thumbnail image that captures the essence of this post.

        Requirements:
        - Create a minimalist, modern composition
        - Use a clean, professional style
        - Include one clear focal point
        - Use soft, professional lighting
        - Maintain ample negative space
        - Avoid text or complex details
        - Ensure it works at small sizes
        - Use a professional color palette

        Blog Title: {title}
        Blog Content: {content}

        Respond with ONLY the image description, nothing else."""

        completion = openai_client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better image descriptions
            messages=[
                {"role": "system", "content": "You are an expert visual designer specializing in creating professional blog thumbnails."},
                {"role": "user", "content": prompt}
            ]
        )
        
        image_description = completion.choices[0].message.content.strip()
        logger.info(f"Generated image description: {image_description}")

        # Generate image using DALL-E with retries
        for attempt in range(max_retries):
            try:
                response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=image_description,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"DALL-E generation attempt {attempt + 1} failed: {str(e)}")
                time.sleep(retry_delay)

        # Download the image with retries
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        image_response = session.get(image_url, timeout=30)
        image_response.raise_for_status()

        # Verify image content
        if not image_response.content or len(image_response.content) < 1000:
            raise ValueError("Downloaded image appears to be invalid or empty")

        # Generate a unique filename with client subfolder
        client_folder = f"thumbnails/{client_obj.id}"
        filename = f"{client_folder}/{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        try:
            # Upload to S3
            import boto3
            s3 = boto3.client('s3')
            
            # Ensure the client folder exists
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=f"{client_folder}/",
                Body=''
            )
            
            # Upload the image
            s3.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=filename,
                Body=image_response.content,
                ContentType='image/png',
                ACL='public-read'  # Make the image publicly accessible
            )
            
            # Verify the upload
            s3.head_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=filename
            )
            
            # Return the S3 URL
            return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{filename}"
            
        except Exception as e:
            logger.error(f"S3 upload error: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error generating thumbnail: {str(e)}")
        logger.exception(e)  # Log full traceback
        return None

def generate_blog_posts_sync(client_id=None):
    """
    Synchronous version of blog post generation
    Returns the created BlogPost object or None if unsuccessful
    """
    # Get API key from environment first, then settings
    api_key = os.getenv('OPENAI_API_KEY') or settings.OPENAI_API_KEY
    if not api_key:
        logger.error("No OpenAI API key found")
        raise ValueError("OpenAI API key not configured")

    logger.info(f"Using API key ending in ...{api_key[-4:]}")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    if client_id:
        try:
            client_obj = Client.objects.get(id=client_id)
            if not client_obj.is_active:
                return None
            
            # Check for relevant events and subjects to avoid
            relevant_event = get_relevant_event()
            avoid_subjects = get_avoid_subjects(client_obj)
            
            # Prepare the system message with tone of voice examples
            system_message = client_obj.gpt_prompt + "\n\n"
            if client_obj.tone_of_voice:
                system_message += client_obj.tone_of_voice.get_formatted_examples()
            system_message += "\nPlease generate a blog post that matches this tone of voice for a client named " + client_obj.name

            if relevant_event:
                system_message += f"\nImportant: Consider incorporating or referencing this upcoming event if relevant: {relevant_event.name} ({relevant_event.date}). Event description: {relevant_event.description}"
            
            if avoid_subjects:
                system_message += f"\nPlease avoid these recently covered subjects: {', '.join(avoid_subjects)}"
            
            system_message += "\nPlease write this blog post in a natural, professional style that feels authentic and engaging. Use varied sentence structures, occasional conversational transitions, and industry-appropriate analogies to make the content more relatable while maintaining credibility. Aim for a warm, knowledgeable voice that builds trust with readers. Keep it aligned with the provided tone of voice examples."

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
            title = full_content.split('\n')[0].replace('Title: ', '')
            content = '\n'.join(full_content.split('\n')[1:]).strip()
            
            # Generate thumbnail image
            thumbnail_url = generate_thumbnail(client_obj, title, content)
            
            # Create blog post
            blog_post = BlogPost.objects.create(
                client=client_obj,
                title=title,
                content=content,
                thumbnail=thumbnail_url,
                status='published',
                published_at=timezone.now(),
                related_event=relevant_event if relevant_event else None
            )
            
            # Extract and save subjects
            extracted_subjects = extract_subjects(content)
            for subject_name in extracted_subjects:
                subject, created = BlogSubject.objects.get_or_create(
                    name=subject_name,
                    client=client_obj,
                    defaults={'usage_count': 1}
                )
                if not created:
                    subject.usage_count += 1
                    subject.save()
                blog_post.subjects.add(subject)
            
            # Check AI score synchronously
            check_ai_score(blog_post.id)
            
            # Update client's last post time
            client_obj.last_post_generated = timezone.now()
            client_obj.save()
            
            return blog_post
            
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            error_post = BlogPost.objects.create(
                client=client_obj,
                title="Error Generating Post",
                content="",
                thumbnail=None,
                status='error',
                error_message=str(e)
            )
            return error_post
    return None

@shared_task
def generate_blog_posts(client_id=None):
    """
    Asynchronous version of blog post generation
    Runs every minute to check for posts that need to be generated
    """
    if client_id:
        return generate_blog_posts_sync(client_id)
    
    current_time = timezone.localtime(timezone.now())
    
    # Get all active clients whose post_time matches current time
    clients = Client.objects.filter(
        is_active=True,
        post_time__hour=current_time.hour,
        post_time__minute=current_time.minute
    )
    
    for client_obj in clients:
        # Double check if post is actually due using the full logic
        next_post_time = client_obj.get_next_post_datetime()
        if next_post_time.date() == current_time.date():  # Only generate if it's due today
            if client_obj.is_due_for_post():
                generate_blog_posts_sync(client_obj.id)

@shared_task
def retry_failed_posts():
    """
    Retry generating posts that previously failed
    """
    # Get the latest failed post for each client
    failed_posts = BlogPost.objects.filter(
        status='error'
    ).order_by('client_id', '-created_at').distinct('client_id')
    
    for post in failed_posts:
        client_obj = post.client
        if client_obj.is_due_for_post():
            try:
                # Generate new post using the sync function
                new_post = generate_blog_posts_sync(client_obj.id)
                if new_post and new_post.status == 'published':
                    # Delete the failed post if new one was successful
                    post.delete()
            except Exception as e:
                logger.error(f"Error retrying failed post for client {client_obj.name}: {str(e)}")
                continue