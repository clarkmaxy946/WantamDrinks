# payments/urls.py
from django.urls import path
from .views import (
    InitiatePaymentView,
    MpesaCallbackView,
    PaymentStatusView,
    CustomerPaymentHistoryView,
    AdminPaymentListView,
    AdminPaymentDetailView,
)

urlpatterns = [
    # Customer endpoints
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/callback/', MpesaCallbackView.as_view(), name='payment-callback'),
    path('payments/history/', CustomerPaymentHistoryView.as_view(), name='payment-history'),
    path('payments/<str:payment_id>/status/', PaymentStatusView.as_view(), name='payment-status'),

    # Admin endpoints
    path('admin/payments/', AdminPaymentListView.as_view(), name='admin-payments'),
    path('admin/payments/<str:payment_id>/', AdminPaymentDetailView.as_view(), name='admin-payment-detail'),
]