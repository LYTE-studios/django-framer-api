from django.db import models
from django.utils import timezone

class Client(models.Model):
    name = models.CharField(max_length=200)
    gpt_prompt = models.TextField(help_text="Custom GPT prompt for this client's tone of voice")
    post_interval_hours = models.IntegerField(default=24, help_text="Hours between each blog post generation")
    last_post_generated = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_due_for_post(self):
        if not self.last_post_generated:
            return True
        
        next_post_due = self.last_post_generated + timezone.timedelta(hours=self.post_interval_hours)
        return timezone.now() >= next_post_due

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
