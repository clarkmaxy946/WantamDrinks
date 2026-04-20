# payments/urls.py
from django.urls import path
from .views import (
    InitiatePaymentView,
    MpesaCallbackView,
    PaymentStatusView,
    CustomerPaymentHistoryView,
    AdminPaymentListView,
    AdminPaymentDetailView,
    TimeoutPaymentView,
    AdminCancelPaymentView,
)

urlpatterns = [
    # Customer endpoints
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/callback/', MpesaCallbackView.as_view(), name='payment-callback'),
    path('payments/history/', CustomerPaymentHistoryView.as_view(), name='payment-history'),
    path('payments/<str:payment_id>/status/', PaymentStatusView.as_view(), name='payment-status'),
    path('payments/<str:payment_id>/timeout/', TimeoutPaymentView.as_view(), name='payment-timeout'),

    # Admin endpoints
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin-payments'),
    path('admin/payments/<str:payment_id>/', AdminPaymentDetailView.as_view(), name='admin-payment-detail'),
    path('admin/payments/<str:payment_id>/cancel/', AdminCancelPaymentView.as_view(), name='admin-payment-cancel'),
]