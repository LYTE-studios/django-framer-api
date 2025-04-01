from django.db import models
from django.utils import timezone

class ToneOfVoice(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(help_text="Description of this tone of voice")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_formatted_examples(self):
        """Get the examples in a format suitable for GPT prompt"""
        examples = self.example_posts.all()
        if not examples:
            return ""
        
        formatted = "Here are some example posts in the desired tone of voice:\n\n"
        for i, example in enumerate(examples, 1):
            formatted += f"Example {i}:\n"
            formatted += f"Title: {example.title}\n"
            formatted += f"Content:\n{example.content}\n\n"
        return formatted

class ToneOfVoiceExample(models.Model):
    tone_of_voice = models.ForeignKey(ToneOfVoice, on_delete=models.CASCADE, related_name='example_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tone_of_voice.name} - {self.title}"

class Client(models.Model):
    name = models.CharField(max_length=200)
    tone_of_voice = models.ForeignKey(ToneOfVoice, on_delete=models.SET_NULL, null=True, related_name='clients')
    gpt_prompt = models.TextField(help_text="Description of the client's needs and industry-specific requirements")
    post_interval_days = models.IntegerField(default=1, help_text="Days between each blog post generation")
    post_time = models.TimeField(default=timezone.datetime.strptime('09:00', '%H:%M').time(), help_text="Time of day to post (24-hour format)")
    last_post_generated = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_due_for_post(self):
        if not self.last_post_generated:
            return True
        
        # Get the date of the last post
        last_post_date = self.last_post_generated.date()
        
        # Calculate the next post date
        next_post_date = last_post_date + timezone.timedelta(days=self.post_interval_days)
        current_time = timezone.localtime(timezone.now())
        
        # Check if we're on or past the next post date and if current time is past post time
        return (current_time.date() > next_post_date or 
                (current_time.date() == next_post_date and 
                 current_time.time() >= self.post_time))

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('error', 'Error'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='blog_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    ai_score = models.FloatField(null=True, blank=True, help_text="AI detection score (0-100, lower is more human-like)")

    def __str__(self):
        return f"{self.client.name} - {self.title}"

    class Meta:
        ordering = ['-created_at']
