from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.command_center, name='command_center'),
    path('bay/', views.inventory_bay, name='inventory_bay'),
    path('product/add/', views.add_product, name='add_product'),
    path('product/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('product/<int:product_id>/stock/', views.update_stock, name='update_stock'),
    path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),
    path('product/<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    path('reviews/', views.all_reviews, name='all_reviews'),
    path('review/<int:review_id>/moderate/', views.moderate_review, name='moderate_review'),
    path('systems/', views.systems, name='systems'),
    path('settings/update/', views.update_settings, name='update_settings'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('coupons/', views.manage_coupons, name='manage_coupons'),
    path('wishlist/', views.wishlist_page, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
]
