# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('admin-register/', views.AdminRegisterView.as_view(), name='admin_register'),
    path('logout/', views.logout_view, name='logout'),

    # Custom password reset views (show link on screen instead of email)
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset_custom'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done_custom'),
]