from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Post, Comment, Like, Follow, Notification

User = get_user_model()


# ==================== USER SERIALIZERS ====================

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'bio', 'profile_picture']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'bio': {'required': False},
            'profile_picture': {'required': False},
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        optional_fields = ['profile_picture', 'bio', 'first_name', 'last_name']
        for field in optional_fields:
            if field in validated_data and not validated_data[field]:
                validated_data.pop(field)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', ''),
            profile_picture=validated_data.get('profile_picture', '')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'bio', 'profile_picture', 'cover_photo', 'website', 'location',
            'is_verified', 'last_active', 'date_joined',
            'followers_count', 'following_count', 'posts_count', 'is_following'
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified', 'last_active', 
                           'followers_count', 'following_count', 'posts_count', 'is_following']
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_posts_count(self, obj):
        return obj.posts.count()
    
    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        return obj.username
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=obj).exists()
        return False


# ==================== POST SERIALIZER ====================

class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    author_profile_picture = serializers.ReadOnlyField(source='user.profile_picture')
    author_is_verified = serializers.ReadOnlyField(source='user.is_verified')
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'media', 'visibility', 'is_pinned',
            'author', 'author_id', 'author_profile_picture', 'author_is_verified',
            'created_at', 'updated_at', 'likes_count', 'comments_count',
            'is_liked', 'is_author'
        ]
        read_only_fields = [
            'id', 'author', 'author_id', 'author_profile_picture', 'author_is_verified',
            'created_at', 'updated_at', 'likes_count', 'comments_count', 
            'is_liked', 'is_author'
        ]
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
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


# ==================== COMMENT SERIALIZER ====================

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    author_profile_picture = serializers.ReadOnlyField(source='user.profile_picture')
    author_is_verified = serializers.ReadOnlyField(source='user.is_verified')
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_id', 'author_profile_picture', 'author_is_verified',
            'post', 'created_at', 'updated_at', 'is_author'
        ]
        read_only_fields = [
            'id', 'author', 'author_id', 'author_profile_picture', 'author_is_verified',
            'post', 'created_at', 'updated_at', 'is_author'
        ]
    
    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


# ==================== LIKE SERIALIZER ====================

class LikeSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'user_id', 'post', 'created_at']
        read_only_fields = ['id', 'user', 'user_id', 'created_at']


# ==================== FOLLOW SERIALIZER ====================

class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.ReadOnlyField(source='follower.username')
    follower_id = serializers.ReadOnlyField(source='follower.id')
    follower_profile_picture = serializers.ReadOnlyField(source='follower.profile_picture')
    following = serializers.ReadOnlyField(source='following.username')
    following_id = serializers.ReadOnlyField(source='following.id')
    following_profile_picture = serializers.ReadOnlyField(source='following.profile_picture')
    
    class Meta:
        model = Follow
        fields = [
            'id', 'follower', 'follower_id', 'follower_profile_picture',
            'following', 'following_id', 'following_profile_picture', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ==================== NOTIFICATION SERIALIZER ====================

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'actor', 'verb', 'target_id', 'target_type', 'timestamp', 'read']