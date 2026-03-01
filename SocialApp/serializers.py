from .models import User, Post, Follow, Like, Comment
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model= User
        fields = ['id', 'username', 'email', 'bio', 'profile_picture', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'profile_picture', 'bio']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
        
class PostSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source= 'user.username')
    user_id = serializers.ReadOnlyField(source = 'user.id')
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id','title', 'content', 'user', 'user_id', 'media', 'created_at', 'updated_at', 'likes_count', 'comments_count']
        read_only_fields= ['id', 'created_at', 'updated_at', 'likes_count', 'comments_count']

    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    

class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.ReadOnlyField(source= 'follower.username')
    following = serializers.ReadOnlyField(source= 'following.username')

    class Meta:
        model= Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'created_at']

class LikeSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']
        read_only_fields = ['id', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model= Comment
        fields = ['id', 'user', 'user_id', 'content', 'post', 'created_at', 'updated_at']