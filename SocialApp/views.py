from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User, Post, Comment, Like, Follow
from .serializers import (
    UserSerializer, UserRegistrationSerializer, PostSerializer,
    CommentSerializer, LikeSerializer, FollowSerializer
)


# ========== HOME VIEW ==========
def home(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Welcome to E-Chat API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'register': '/auth/register/',
                'login': '/auth/login/',
                'refresh': '/auth/refresh/',
            },
            'users': {
                'list': '/users/',
                'detail': '/users/{id}/',
                'followers': '/users/{id}/followers/',
                'following': '/users/{id}/following/',
            },
            'posts': {
                'list': '/posts/',
                'detail': '/posts/{id}/',
                'like': '/posts/{id}/like/',
                'comments': '/posts/{id}/comments/',
            },
            'comments': {
                'detail': '/comments/{id}/',
            },
            'feed': '/feed/',
            'follow': '/follow/{id}/',
        }
    })


# ========== AUTHENTICATION VIEWS ==========
class UserRegistrationView(generics.CreateAPIView):
    """
    User registration endpoint
    POST /auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bio': user.bio,
                'profile_picture': user.profile_picture,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ========== USER VIEWS ==========
class UserListView(generics.ListAPIView):
    """
    List all users
    GET /users/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Optional search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        return queryset


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile
    GET /users/{id}/
    PATCH /users/{id}/
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_update(self, serializer):
        if self.get_object() != self.request.user:
            raise PermissionDenied("You can only update your own profile")
        serializer.save()


# ========== POST VIEWS ==========
class PostListCreateView(generics.ListCreateAPIView):
    """
    List all posts or create a new post
    GET /posts/
    POST /posts/
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Post.objects.all()
        # Optional filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete a post
    GET /posts/{id}/
    PATCH /posts/{id}/
    DELETE /posts/{id}/
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_update(self, serializer):
        post = self.get_object()
        if post.user != self.request.user:
            raise PermissionDenied("You can only update your own posts")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own posts")
        instance.delete()


# ========== FEED VIEW ==========
class FeedView(generics.ListAPIView):
    """
    Get posts from users you follow
    GET /feed/
    """
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
    """
    Follow or unfollow a user
    POST /follow/{user_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        """Follow or unfollow a user"""
        user_to_follow = get_object_or_404(User, id=user_id)
        
        # Prevent self-follow
        if request.user == user_to_follow:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already following
        follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        ).first()
        
        if follow:
            # Unfollow
            follow.delete()
            return Response({
                'following': False,
                'followers_count': user_to_follow.followers.count(),
                'user_id': user_id
            }, status=status.HTTP_200_OK)
        else:
            # Follow
            follow = Follow.objects.create(
                follower=request.user,
                following=user_to_follow
            )
            return Response({
                'following': True,
                'followers_count': user_to_follow.followers.count(),
                'user_id': user_id
            }, status=status.HTTP_201_CREATED)


class FollowersListView(generics.ListAPIView):
    """
    Get followers of a user
    GET /users/{user_id}/followers/
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user.followers.all()


class FollowingListView(generics.ListAPIView):
    """
    Get users that a user follows
    GET /users/{user_id}/following/
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user.following.all()


# ========== LIKE VIEWS ==========
class LikeToggleView(APIView):
    """
    Like or unlike a post
    POST /posts/{post_id}/like/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        """Like or unlike a post"""
        post = get_object_or_404(Post, id=post_id)
        
        # Check if already liked
        like = Like.objects.filter(
            user=request.user,
            post=post
        ).first()
        
        if like:
            # Unlike
            like.delete()
            return Response({
                'liked': False,
                'likes_count': post.likes.count(),
                'post_id': post_id
            }, status=status.HTTP_200_OK)
        else:
            # Like
            like = Like.objects.create(
                user=request.user,
                post=post
            )
            return Response({
                'liked': True,
                'likes_count': post.likes.count(),
                'post_id': post_id
            }, status=status.HTTP_201_CREATED)


# ========== COMMENT VIEWS ==========
class CommentListCreateView(generics.ListCreateAPIView):
    """
    List comments on a post or create a new comment
    GET /posts/{post_id}/comments/
    POST /posts/{post_id}/comments/
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id).order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get, update, or delete a comment
    GET /comments/{id}/
    PATCH /comments/{id}/
    DELETE /comments/{id}/
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.user != self.request.user:
            raise PermissionDenied("You can only update your own comments")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own comments")
        instance.delete()