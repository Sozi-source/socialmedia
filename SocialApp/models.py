from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import os
import uuid

def user_profile_picture_path(instance, filename):
    """Generate path for user profile pictures"""
    ext = filename.split('.')[-1]
    return f'users/{instance.id}/profile_{timezone.now().timestamp()}.{ext}'

def user_cover_photo_path(instance, filename):
    """Generate path for user cover photos"""
    ext = filename.split('.')[-1]
    return f'users/{instance.id}/cover_{timezone.now().timestamp()}.{ext}'

def post_media_path(instance, filename):
    """Generate path for post media - ensures directory exists"""
    ext = filename.split('.')[-1]
    timestamp = timezone.now().timestamp()
    # Use UUID for unique filename to avoid conflicts
    unique_id = uuid.uuid4().hex[:8]
    return f'posts/{timestamp}_{unique_id}.{ext}'


class User(AbstractUser):
    bio = models.TextField(max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_path, 
        blank=True, 
        null=True,
        max_length=500
    )
    cover_photo = models.ImageField(
        upload_to=user_cover_photo_path, 
        blank=True, 
        null=True,
        max_length=500
    )
    website = models.URLField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    last_active = models.DateTimeField(default=timezone.now)

    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username
    
    @property
    def followers_count(self):
        return self.followers.count()
    
    @property
    def following_count(self):
        return self.following.count()
    
    @property
    def posts_count(self):
        return self.posts.count()


class Post(models.Model):
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('followers', 'Followers Only'),
        ('private', 'Only Me'),
    )
    
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(max_length=500, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='posts'
    )
    visibility = models.CharField(
        max_length=10, 
        choices=VISIBILITY_CHOICES, 
        default='public'
    )
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
        return f"Post by {self.user.username}"
    
    @property
    def likes_count(self):
        return self.likes.count()
    
    @property
    def comments_count(self):
        return self.comments.count()


class PostMedia(models.Model):
    """Model for post media (images, videos, etc.)"""
    MEDIA_TYPE_CHOICES = (
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
    )
    
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='media_items'
    )
    file = models.FileField(
        upload_to=post_media_path,
        max_length=500
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    thumbnail = models.ImageField(
        upload_to='post_thumbnails/',
        blank=True,
        null=True
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['post', 'order']),
        ]
    
    def __str__(self):
        return f"Media for post {self.post.id}"


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField(max_length=500)
    media = models.FileField(
        upload_to='comment_media/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['parent', '-created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username}"


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='likes'
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"


class Follow(models.Model):
    following = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    follower = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['follower', 'following'])
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('mention', 'Mention'),
        ('share', 'Share'),
        ('reply', 'Reply'),
    )
    
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    actor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='actor_notifications'
    )
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