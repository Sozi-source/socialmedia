from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Post, PostMedia, Comment, Like, Follow, Notification

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'bio']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture', 'cover_photo',
                  'website', 'location', 'is_verified', 'last_active', 'date_joined',
                  'followers_count', 'following_count', 'posts_count', 'is_following']
    
    def get_followers_count(self, obj): return obj.followers.count()
    def get_following_count(self, obj): return obj.following.count()
    def get_posts_count(self, obj): return obj.posts.count()
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False


class PostMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PostMedia
        fields = ['id', 'file_url', 'media_type', 'order', 'created_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    author_profile_picture = serializers.SerializerMethodField()
    author_is_verified = serializers.ReadOnlyField(source='user.is_verified')
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    media_items = PostMediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'visibility', 'is_pinned', 'author', 'author_id',
                  'author_profile_picture', 'author_is_verified', 'created_at', 'updated_at',
                  'likes_count', 'comments_count', 'is_liked', 'is_author', 'media_items']
    
    def get_author_profile_picture(self, obj):
        if obj.user.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile_picture.url)
        return None
    
    def get_likes_count(self, obj): return obj.likes.count()
    def get_comments_count(self, obj): return obj.comments.count()
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    author_profile_picture = serializers.SerializerMethodField()
    author_is_verified = serializers.ReadOnlyField(source='user.is_verified')
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'author_id', 'author_profile_picture', 'author_is_verified',
                  'post', 'parent', 'created_at', 'updated_at', 'is_author']
    
    def get_author_profile_picture(self, obj):
        if obj.user.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.profile_picture.url)
        return None
    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'actor', 'verb', 'target_id', 'target_type', 'timestamp', 'read']