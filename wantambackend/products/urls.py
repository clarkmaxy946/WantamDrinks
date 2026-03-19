# products/urls.py
from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    AdminProductListView,
    AdminProductDetailView,
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='products'),
    path('products/<str:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('admin/products/', AdminProductListView.as_view(), name='admin-products'),
    path('admin/products/<str:product_id>/', AdminProductDetailView.as_view(), name='admin-product-detail'),
]