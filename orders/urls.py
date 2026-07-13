from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.create_order, name='create_order'),
    path('coupon/validate/', views.validate_coupon, name='validate_coupon'),
    path('', views.orbital_orders, name='orbital_orders'),
    path('<str:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    path('<str:order_id>/', views.order_detail, name='order_detail'),
    path('<str:order_id>/status/', views.update_status, name='update_status'),
    path('<str:order_id>/delete/', views.delete_order, name='delete_order'),
]
