# alerts/urls.py
from django.urls import path
from .views import (
    AdminAlertListView,
    AdminAlertDetailView,
    AdminAlertResolveView,
    AdminAlertSummaryView,
)

urlpatterns = [
    # Static paths before dynamic paths
    path('admin/alerts/', AdminAlertListView.as_view(), name='admin-alerts'),
    path('admin/alerts/summary/', AdminAlertSummaryView.as_view(), name='admin-alerts-summary'),
    path('admin/alerts/<int:alert_id>/', AdminAlertDetailView.as_view(), name='admin-alert-detail'),
    path('admin/alerts/<int:alert_id>/resolve/', AdminAlertResolveView.as_view(), name='admin-alert-resolve'),
]