from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_picture = models.URLField(max_length=500, blank=True)
    cover_photo = models.URLField(max_length=500, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    last_active = models.DateTimeField(default=timezone.now)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
    
class Post(models.Model):
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('followers', 'Followers Only'),
        ('private', 'Only Me'),
    )
    
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(max_length=500, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    media = models.URLField(max_length=500, blank=True, null=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['visibility', '-created_at']),
        ]

    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at}"
    
class Follow(models.Model):
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['follower', 'following'])
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"
    
class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.id}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('share', 'Share'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor_notifications')
    verb = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_type = models.CharField(max_length=20, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['recipient', '-timestamp']),
            models.Index(fields=['recipient', 'read']),
        ]
    
    def __str__(self):
        return f"{self.actor.username} {self.verb} {self.recipient.username}"