from django.db import models
from django.utils import timezone

class Client(models.Model):
    name = models.CharField(max_length=200)
    gpt_prompt = models.TextField(help_text="Custom GPT prompt for this client's tone of voice")
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

    def __str__(self):
        return f"{self.client.name} - {self.title}"

    class Meta:
        ordering = ['-created_at']
