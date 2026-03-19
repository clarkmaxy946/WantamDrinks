# inventory/urls.py
from django.urls import path
from .views import (
    BranchInventoryView,
    AdminInventoryListView,
    AdminLowStockView,
    AdminBranchInventoryView,
    AdminInventoryDetailView,
    AdminRestockView,
    AdminRestockLogView,
)

urlpatterns = [
    # Customer
    path('inventory/<str:branch_id>/', BranchInventoryView.as_view(), name='branch-inventory'),

    # Admin — static paths must come before dynamic paths
    path('admin/inventory/', AdminInventoryListView.as_view(), name='admin-inventory'),
    path('admin/inventory/low-stock/', AdminLowStockView.as_view(), name='admin-low-stock'),
    path('admin/inventory/logs/', AdminRestockLogView.as_view(), name='admin-restock-logs'),
    path('admin/inventory/<str:branch_id>/', AdminBranchInventoryView.as_view(), name='admin-branch-inventory'),
    path('admin/inventory/<str:branch_id>/<str:product_id>/', AdminInventoryDetailView.as_view(), name='admin-inventory-detail'),
    path('admin/inventory/<str:branch_id>/<str:product_id>/restock/', AdminRestockView.as_view(), name='admin-restock'),
]