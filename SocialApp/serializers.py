from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Post, Comment, Like, Follow

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Confirm password"
    )
    
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
        """Validate password strength"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Validate that password and password2 match"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create and return a new user"""
        # Remove password2 from validated_data
        validated_data.pop('password2')
        
        # Remove empty strings for optional fields
        if 'profile_picture' in validated_data and not validated_data['profile_picture']:
            validated_data.pop('profile_picture')
        
        if 'bio' in validated_data and not validated_data['bio']:
            validated_data.pop('bio')
        
        if 'first_name' in validated_data and not validated_data['first_name']:
            validated_data.pop('first_name')
        
        if 'last_name' in validated_data and not validated_data['last_name']:
            validated_data.pop('last_name')
        
        # Create user with the provided data
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
    """
    Serializer for User model - used for displaying user information
    """
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'bio', 'profile_picture', 'date_joined',
            'followers_count', 'following_count', 'posts_count'
        ]
        read_only_fields = ['id', 'date_joined', 'followers_count', 'following_count', 'posts_count']
    
    def get_followers_count(self, obj):
        """Get number of followers"""
        return obj.followers.count()
    
    def get_following_count(self, obj):
        """Get number of users this user follows"""
        return obj.following.count()
    
    def get_posts_count(self, obj):
        """Get number of posts by this user"""
        return obj.posts.count()
    
    def get_full_name(self, obj):
        """Get user's full name"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        return obj.username


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model
    """
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    author_profile_picture = serializers.ReadOnlyField(source='user.profile_picture')
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'media', 'author', 'author_id', 'author_profile_picture',
            'created_at', 'updated_at', 'likes_count', 'comments_count',
            'is_liked', 'is_author'
        ]
        read_only_fields = [
            'id', 'author', 'author_id', 'author_profile_picture', 'created_at', 'updated_at',
            'likes_count', 'comments_count', 'is_liked', 'is_author'
        ]
    
    def get_likes_count(self, obj):
        """Get number of likes on this post"""
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        """Get number of comments on this post"""
        return obj.comments.count()
    
    def get_is_liked(self, obj):
        """Check if current user has liked this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_is_author(self, obj):
        """Check if current user is the author of this post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model
    """
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    author_profile_picture = serializers.ReadOnlyField(source='user.profile_picture')
    is_author = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_id', 'author_profile_picture',
            'post', 'created_at', 'updated_at', 'is_author'
        ]
        read_only_fields = ['id', 'author', 'author_id', 'author_profile_picture', 'created_at', 'updated_at', 'is_author']
    
    def get_is_author(self, obj):
        """Check if current user is the author of this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False


class LikeSerializer(serializers.ModelSerializer):
    """
    Serializer for Like model
    """
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'user_id', 'post', 'created_at']
        read_only_fields = ['id', 'user', 'user_id', 'created_at']


class FollowSerializer(serializers.ModelSerializer):
    """
    Serializer for Follow model
    """
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