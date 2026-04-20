from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

_dashboard       = TemplateView.as_view(template_name='dashboard.html')
_admin_dashboard = TemplateView.as_view(template_name='admin_dashboard.html')

urlpatterns = [
    path('admin/', admin.site.urls),   # Django built-in admin — untouched

    path('api/', include('users.urls')),
    path('api/', include('branches.urls')),
    path('api/', include('products.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('alerts.urls')),
    path('api/', include('analytics.urls')),

    path('',          TemplateView.as_view(template_name='index.html'),    name='landing-page'),
    path('login/',    TemplateView.as_view(template_name='login.html'),    name='login-page'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register-page'),
    path('forgot/',   TemplateView.as_view(template_name='forgot_and_reset.html')),
    path('reset-password/<str:uidb64>/<str:token>/',
         TemplateView.as_view(template_name='forgot_and_reset.html')),

    # Customer dashboard SPA
    path('dashboard/',    _dashboard, name='dashboard-page'),
    path('profile/',      _dashboard, name='profile-page'),
    path('transactions/', _dashboard, name='transactions-page'),
    path('order/',        _dashboard, name='order-page'),
    path('payment/',      _dashboard, name='payment-page'),

    # ── Admin dashboard SPA — all routes under /admin_dashboard/ ──────────
    path('admin_dashboard/',                        _admin_dashboard, name='admin-dashboard-page'),
    path('admin_dashboard/users/',                  _admin_dashboard),
    path('admin_dashboard/branches/',               _admin_dashboard),
    path('admin_dashboard/products/',               _admin_dashboard),
    path('admin_dashboard/inventory/',              _admin_dashboard),
    path('admin_dashboard/restock/',                _admin_dashboard),
    path('admin_dashboard/restock/action/',         _admin_dashboard),
    path('admin_dashboard/restock/log/',            _admin_dashboard),
    path('admin_dashboard/transactions/',           _admin_dashboard),
    path('admin_dashboard/transactions/orders/',    _admin_dashboard),
    path('admin_dashboard/transactions/payments/',  _admin_dashboard),
    path('admin_dashboard/analytics/',              _admin_dashboard),
    path('admin_dashboard/analytics/daily/',        _admin_dashboard),
    path('admin_dashboard/analytics/monthly/',      _admin_dashboard),
    path('admin_dashboard/alerts/',                 _admin_dashboard),
]