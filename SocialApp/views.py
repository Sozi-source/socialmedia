from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Post, User, Comment, Like, Follow
from .serializers import UserSerializer, UserRegistrationSerializer, FollowSerializer, PostSerializer, CommentSerializer, LikeSerializer
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse

# Create your views here.
# ROOT API
def home(request):
    return JsonResponse({
        'message': 'Welcome to SocialMedia API',
        'endpoints': [
            '/admin/',
            '/api/auth/register/',
            '/api/auth/login/',
            '/api/users/',
            '/api/posts/',
            '/api/feed/',
        ]
    })

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[IsAuthenticated]

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.get_object() != self.request.user:
            raise PermissionDenied("You can only update your own profile")
        serializer.save()

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes =[IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes =[IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        post = self.get_object()
        if post.user != self.request.user:
            raise self.permission_denied("You can only update your own post")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own post")
        instance.delete()

    # ========== FEED VIEW ==========
class FeedView(generics.ListAPIView):
    """View posts from users you follow"""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get users that the current user follows
        following_users = Follow.objects.filter(
            follower=self.request.user
        ).values_list('following', flat=True)
        
        # Return posts from followed users and own posts
        return Post.objects.filter(
            Q(user__in=following_users) | Q(user=self.request.user)
        ).order_by('-created_at')

# ========== FOLLOW VIEWS ==========
class FollowToggleView(APIView):
    """Follow or unfollow a user"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        """Follow a user"""
        user_to_follow = get_object_or_404(User, id=user_id)
        
        # Prevent self-follow
        if request.user == user_to_follow:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create follow relationship
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            serializer = FollowSerializer(follow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "You are already following this user"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, user_id):
        """Unfollow a user"""
        user_to_unfollow = get_object_or_404(User, id=user_id)
        
        follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).first()
        
        if follow:
            follow.delete()
            return Response(
                {"message": "Successfully unfollowed user"},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"error": "You are not following this user"},
                status=status.HTTP_400_BAD_REQUEST
            )

class FollowersListView(generics.ListAPIView):
    """List users who follow a specific user"""
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(following_id=user_id).select_related('follower')

class FollowingListView(generics.ListAPIView):
    """List users that a specific user follows"""
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Follow.objects.filter(follower_id=user_id).select_related('following')

# ========== LIKE VIEWS ==========
class LikeToggleView(APIView):
    """Like or unlike a post"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        """Like a post"""
        post = get_object_or_404(Post, id=post_id)
        
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if created:
            serializer = LikeSerializer(like)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {"error": "You already liked this post"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request, post_id):
        """Unlike a post"""
        post = get_object_or_404(Post, id=post_id)
        
        like = Like.objects.filter(
            user=request.user,
            post=post
        ).first()
        
        if like:
            like.delete()
            return Response(
                {"message": "Successfully unliked post"},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"error": "You haven't liked this post"},
                status=status.HTTP_400_BAD_REQUEST
            )

# ========== COMMENT VIEWS ==========
class CommentListCreateView(generics.ListCreateAPIView):
    """List comments on a post or create a new comment"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id).order_by('-created_at')
    
    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)

class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a comment"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own comments")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own comments")
        instance.delete()