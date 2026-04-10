"""
URL configuration for wantambackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/', include('branches.urls')),
    path('api/', include('products.urls')),
    path('api/', include('inventory.urls')),
    path('api/', include('orders.urls')),
    path('api/', include('payments.urls')),
    path('api/', include('alerts.urls')),
    path('api/', include('analytics.urls')),
    
    path('', TemplateView.as_view(template_name='index.html'), name='landing-page'),
    path('login/',        TemplateView.as_view(template_name='login.html'),    name='login-page'),
    path('register/',     TemplateView.as_view(template_name='register.html'), name='register-page'),
    path('dashboard/',    TemplateView.as_view(template_name='dashboard.html'), name='dashboard-page'),
    path('profile/',   TemplateView.as_view(template_name='profile_panel.html'),   name='profile-page'),
    path('payment/',      TemplateView.as_view(template_name='payment.html'),  name='payment-page'),
    
    # Both routes serve the same HTML file
    path('forgot/', TemplateView.as_view(template_name='forgot_and_reset.html')),
    path('reset-password/<str:uidb64>/<str:token>/', TemplateView.as_view(template_name='forgot_and_reset.html')),
    
]
