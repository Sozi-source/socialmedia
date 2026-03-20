from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User, Post, Comment, Like, Follow, Notification
from .serializers import (
    UserSerializer, UserRegistrationSerializer, PostSerializer,
    CommentSerializer, LikeSerializer, FollowSerializer, NotificationSerializer
)


# ========== HOME VIEW ==========
def home(request):
    return JsonResponse({
        'message': 'Welcome to E-Chat API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {'register': '/auth/register/', 'login': '/auth/login/', 'refresh': '/auth/refresh/'},
            'users': {'list': '/users/', 'detail': '/users/{id}/', 'posts': '/users/{id}/posts/',
                      'followers': '/users/{id}/followers/', 'following': '/users/{id}/following/'},
            'posts': {'list': '/posts/', 'detail': '/posts/{id}/', 'like': '/posts/{id}/like/', 
                      'comments': '/posts/{id}/comments/'},
            'comments': {'detail': '/comments/{id}/'},
            'feed': '/feed/', 'follow': '/follow/{id}/',
            'notifications': '/notifications/'
        }
    })


# ========== AUTHENTICATION VIEWS ==========
class UserRegistrationView(generics.CreateAPIView):
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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | Q(email__icontains=search) |
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        return queryset


class UserDetailView(generics.RetrieveUpdateAPIView):
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


class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Post.objects.filter(user_id=user_id).order_by('-created_at')


# ========== POST VIEWS ==========
class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Post.objects.all()
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
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
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        following_users = Follow.objects.filter(follower=self.request.user).values_list('following', flat=True)
        return Post.objects.filter(
            Q(user__in=following_users, visibility='public') | Q(user=self.request.user)
        ).order_by('-created_at')


# ========== FOLLOW VIEWS ==========
class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, id=user_id)
        
        if request.user == user_to_follow:
            return Response({"error": "You cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
        
        follow = Follow.objects.filter(follower=request.user, following=user_to_follow).first()
        
        if follow:
            follow.delete()
            Notification.objects.filter(recipient=user_to_follow, actor=request.user, verb='follow').delete()
            return Response({
                'following': False,
                'followers_count': user_to_follow.followers.count(),
                'user_id': user_id
            }, status=status.HTTP_200_OK)
        else:
            follow = Follow.objects.create(follower=request.user, following=user_to_follow)
            Notification.objects.create(
                recipient=user_to_follow, actor=request.user, verb='follow',
                target_id=user_to_follow.id, target_type='user'
            )
            return Response({
                'following': True,
                'followers_count': user_to_follow.followers.count(),
                'user_id': user_id
            }, status=status.HTTP_201_CREATED)


class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user.followers.all()


class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user.following.all()


# ========== LIKE VIEWS ==========
class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like = Like.objects.filter(user=request.user, post=post).first()
        
        if like:
            like.delete()
            Notification.objects.filter(recipient=post.user, actor=request.user, verb='like', target_id=post_id).delete()
            return Response({
                'liked': False,
                'likes_count': post.likes.count(),
                'post_id': post_id
            }, status=status.HTTP_200_OK)
        else:
            like = Like.objects.create(user=request.user, post=post)
            if post.user != request.user:
                Notification.objects.create(
                    recipient=post.user, actor=request.user, verb='like',
                    target_id=post.id, target_type='post'
                )
            return Response({
                'liked': True,
                'likes_count': post.likes.count(),
                'post_id': post_id
            }, status=status.HTTP_201_CREATED)


# ========== COMMENT VIEWS ==========
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        
        data = request.data.copy()
        data.pop('post', None)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(user=request.user, post=post)
        
        if post.user != request.user:
            Notification.objects.create(
                recipient=post.user, actor=request.user, verb='comment',
                target_id=comment.id, target_type='comment'
            )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
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


# ========== NOTIFICATION VIEWS ==========
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        notification = get_object_or_404(Notification, id=pk, recipient=request.user)
        notification.read = True
        notification.save()
        return Response({'status': 'marked as read'})


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(recipient=request.user, read=False).update(read=True)
        return Response({'status': 'all marked as read'})


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, read=False).count()
        return Response({'count': count})


class SuggestionsView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        following_ids = Follow.objects.filter(follower=self.request.user).values_list('following_id', flat=True)
        return User.objects.exclude(
            id__in=list(following_ids) + [self.request.user.id]
        ).order_by('-posts_count')[:20]