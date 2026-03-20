import mimetypes
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import generics, status, parsers
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User, Post, PostMedia, Comment, Like, Follow, Notification
from .serializers import (
    UserSerializer, UserRegistrationSerializer, PostSerializer,
    CommentSerializer, LikeSerializer, FollowSerializer, NotificationSerializer,
    PostMediaSerializer
)


def home(request):
    return JsonResponse({'message': 'Welcome to E-Chat API', 'version': '2.0.0'})


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'id': user.id, 'username': user.username, 'email': user.email}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def perform_update(self, serializer):
        if self.get_object() != self.request.user:
            raise PermissionDenied("You can only update your own profile")
        serializer.save()


class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Post.objects.filter(user_id=self.kwargs['user_id']).order_by('-created_at')


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_queryset(self):
        queryset = Post.objects.all()
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset
    
    def get_media_type(self, file):
        mime_type, _ = mimetypes.guess_type(file.name)
        if mime_type and mime_type.startswith('image/'):
            return 'image'
        elif mime_type and mime_type.startswith('video/'):
            return 'video'
        return 'document'
    
    def perform_create(self, serializer):
        post = serializer.save(user=self.request.user)
        files = self.request.FILES.getlist('media')
        for index, file in enumerate(files):
            media_type = self.get_media_type(file)
            PostMedia.objects.create(
                post=post,
                file=file,
                media_type=media_type,
                order=index
            )


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        if self.get_object().user != self.request.user:
            raise PermissionDenied("You can only update your own posts")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own posts")
        instance.delete()


class FeedView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        following_users = Follow.objects.filter(follower=self.request.user).values_list('following', flat=True)
        return Post.objects.filter(
            Q(user__in=following_users) | Q(user=self.request.user)
        ).order_by('-created_at')


class FollowToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_follow = get_object_or_404(User, id=user_id)
        if request.user == user_to_follow:
            return Response({"error": "You cannot follow yourself"}, status=status.HTTP_400_BAD_REQUEST)
        
        follow = Follow.objects.filter(follower=request.user, following=user_to_follow).first()
        if follow:
            follow.delete()
            return Response({'following': False, 'followers_count': user_to_follow.followers.count()}, status=status.HTTP_200_OK)
        else:
            Follow.objects.create(follower=request.user, following=user_to_follow)
            return Response({'following': True, 'followers_count': user_to_follow.followers.count()}, status=status.HTTP_201_CREATED)


class FollowersListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        return user.followers.all()


class FollowingListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        return user.following.all()


class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like = Like.objects.filter(user=request.user, post=post).first()
        
        if like:
            like.delete()
            return Response({'liked': False, 'likes_count': post.likes.count()}, status=status.HTTP_200_OK)
        else:
            Like.objects.create(user=request.user, post=post)
            return Response({'liked': True, 'likes_count': post.likes.count()}, status=status.HTTP_201_CREATED)


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_id'], parent=None).order_by('-created_at')
    
    def perform_create(self, serializer):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        if self.get_object().user != self.request.user:
            raise PermissionDenied("You can only update your own comments")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own comments")
        instance.delete()


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
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        exclude_ids = list(following_ids) + [request.user.id]
        suggested_users = User.objects.exclude(id__in=exclude_ids).order_by('-date_joined')[:10]
        
        data = [{'id': u.id, 'username': u.username, 'profile_picture': u.profile_picture.url if u.profile_picture else None, 'bio': u.bio or '', 'is_verified': u.is_verified} for u in suggested_users]
        return Response(data, status=status.HTTP_200_OK)