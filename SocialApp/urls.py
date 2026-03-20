from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from SocialApp.views import home

urlpatterns = [
    # ========HOME==========
    path('', home, name='home'),
    # ========== AUTHENTICATION ==========
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ========== USERS ==========
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/followers/', views.FollowersListView.as_view(), name='followers'),
    path('users/<int:user_id>/following/', views.FollowingListView.as_view(), name='following'),
    
    # ========== POSTS ==========
    path('posts/', views.PostListCreateView.as_view(), name='post-list'),
    path('posts/<int:pk>/', views.PostRetrieveUpdateDestroyView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/like/', views.LikeToggleView.as_view(), name='like-toggle'),
    path('posts/<int:post_id>/comments/', views.CommentListCreateView.as_view(), name='comment-list'),
    
    # ========== COMMENTS ==========
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDestroyView.as_view(), name='comment-detail'),
    
    # ========== FEED ==========
    path('feed/', views.FeedView.as_view(), name='feed'),
    
    # ========== FOLLOWS ==========
    path('follow/<int:user_id>/', views.FollowToggleView.as_view(), name='follow-toggle'),
]