from django.contrib import admin
from .models import Order, OrderItem, Coupon


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_order_amount',
                    'max_uses', 'used_count', 'is_active', 'valid_from', 'valid_to')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)
    list_editable = ('is_active',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer', 'status', 'original_total', 'discount_amount', 'total', 'coupon', 'created_at')
    list_filter = ('status',)
    search_fields = ('order_id', 'customer__username')
    inlines = [OrderItemInline]
    readonly_fields = ('order_id', 'original_total', 'discount_amount', 'coupon')
