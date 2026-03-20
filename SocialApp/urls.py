from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Users
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/followers/', views.FollowersListView.as_view(), name='followers'),
    path('users/<int:user_id>/following/', views.FollowingListView.as_view(), name='following'),
    
    # Posts
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostRetrieveUpdateDestroyView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/like/', views.LikeToggleView.as_view(), name='like-toggle'),
    path('posts/<int:post_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    
    # Comments
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDestroyView.as_view(), name='comment-detail'),
    
    # Feed
    path('feed/', views.FeedView.as_view(), name='feed'),
    
    # Follows
    path('follow/<int:user_id>/', views.FollowToggleView.as_view(), name='follow-toggle'),
]