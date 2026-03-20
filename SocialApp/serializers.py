from .models import User, Post, Follow, Like, Comment
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio', 'profile_picture', 'date_joined', 
                  'first_name', 'last_name', 'followers_count', 'following_count', 'posts_count']
        read_only_fields = ['id', 'date_joined', 'followers_count', 'following_count', 'posts_count']
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()
    
    def get_posts_count(self, obj):
        return obj.posts.count()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'profile_picture', 'bio', 'first_name', 'last_name']
        extra_kwargs = {
            'profile_picture': {'required': False},
            'bio': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        # Remove password2 from validated_data
        validated_data.pop('password2')
        
        # Create user with the correct fields
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            bio=validated_data.get('bio', ''),
            profile_picture=validated_data.get('profile_picture', None)
        )
        return user


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'content', 'media', 'author', 'author_id', 'created_at', 'updated_at', 
                  'likes_count', 'comments_count', 'is_liked', 'is_author']
        read_only_fields = ['id', 'created_at', 'updated_at', 'likes_count', 'comments_count', 
                           'is_liked', 'is_author']

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


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.ReadOnlyField(source='follower.username')
    follower_id = serializers.ReadOnlyField(source='follower.id')
    following = serializers.ReadOnlyField(source='following.username')
    following_id = serializers.ReadOnlyField(source='following.id')

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'follower_id', 'following', 'following_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = Like
        fields = ['id', 'user', 'user_id', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='user.username')
    author_id = serializers.ReadOnlyField(source='user.id')
    is_author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'author_id', 'content', 'post', 'created_at', 'updated_at', 'is_author']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_author']
    
    def get_is_author(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.user == request.user
        return False