# orders/urls.py
from django.urls import path
from .views import (
    OrderCreateView,
    OrderHistoryView,
    OrderDetailView,
    OrderCancelView,
    AdminOrderListView,
    AdminOrderDetailView,
)

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/history/', OrderHistoryView.as_view(), name='order-history'),
    path('orders/<str:order_id>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<str:order_id>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/orders/<str:order_id>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
]