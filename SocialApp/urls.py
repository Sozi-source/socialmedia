from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('api/register/', views.UserRegistrationView.as_view(), name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Users
    path('api/users/', views.UserListView.as_view(), name='user-list'),
    path('api/users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Posts
    path('api/posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('api/posts/<int:pk>/', views.PostRetrieveUpdateDestroyView.as_view(), name='post-detail'),
    
    # Feed
    path('api/feed/', views.FeedView.as_view(), name='feed'),
    
    # Follows
    path('api/follow/<int:user_id>/', views.FollowToggleView.as_view(), name='follow-toggle'),
    path('api/users/<int:user_id>/followers/', views.FollowersListView.as_view(), name='followers'),
    path('api/users/<int:user_id>/following/', views.FollowingListView.as_view(), name='following'),
    
    # Likes
    path('api/posts/<int:post_id>/like/', views.LikeToggleView.as_view(), name='like-toggle'),
    
    # Comments
    path('api/posts/<int:post_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    path('api/comments/<int:pk>/', views.CommentRetrieveUpdateDestroyView.as_view(), name='comment-detail'),
]