# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    AdminUserListView,
    AdminUserDetailView,
    
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
)




urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<str:user_id>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    
    
    path('auth/forgot-password/',                          PasswordResetRequestView.as_view(),  name='forgot-password'),
    path('auth/reset-password/<uidb64>/<token>/',          PasswordResetConfirmView.as_view(),  name='reset-password'),
    path('auth/change-password/',                          PasswordChangeView.as_view(),        name='change-password'),
    
]