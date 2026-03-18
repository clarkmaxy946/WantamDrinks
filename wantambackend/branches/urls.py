# branches/urls.py
from django.urls import path
from .views import (
    BranchListView,
    AdminBranchListView,
    AdminBranchDetailView,
)

urlpatterns = [
    path('branches/', BranchListView.as_view(), name='branches'),
    path('admin/branches/', AdminBranchListView.as_view(), name='admin-branches'),
    path('admin/branches/<str:branch_id>/', AdminBranchDetailView.as_view(), name='admin-branch-detail'),
]