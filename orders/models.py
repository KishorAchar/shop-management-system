from django.db import models
from accounts.models import User
from inventory.models import Product
from django.utils import timezone


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'orders_coupon'

    def __str__(self):
        return f"{self.code} ({self.discount_type}: {self.discount_value})"

    def is_valid(self):
        import datetime
        from django.utils import timezone as tz
        now = tz.now()

        def safe_aware(dt):
            if dt is None:
                return None
            if isinstance(dt, datetime.datetime) and tz.is_naive(dt):
                return tz.make_aware(dt)
            return dt

        valid_from = safe_aware(self.valid_from)
        valid_to   = safe_aware(self.valid_to)

        if not self.is_active:
            return False, "Coupon is inactive."
        if self.used_count >= self.max_uses:
            return False, "Coupon usage limit reached."
        if valid_to and now > valid_to:
            return False, "Coupon has expired."
        if valid_from and now < valid_from:
            return False, "Coupon is not yet active."
        return True, "Valid"

    def calculate_discount(self, order_total):
        from decimal import Decimal, ROUND_HALF_UP
        total = Decimal(str(order_total))
        if self.discount_type == 'percentage':
            result = total * self.discount_value / Decimal('100')
        else:
            result = min(self.discount_value, total)
        return result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_shipping(subtotal_after_discount):
    """
    Tiered shipping + delivery estimate based on post-discount order value.
      ≥ ₹2000  → FREE  (1–3 days)
      ≥ ₹1000  → ₹49   (2–4 days)
      ≥ ₹500   → ₹79   (3–5 days)
      < ₹500   → ₹99   (4–7 days)
    Returns (shipping_charge: float, delivery_days: str)
    """
    amt = float(subtotal_after_discount)
    if amt >= 2000:
        return 0.0,  "1–3 business days (FREE shipping)"
    elif amt >= 1000:
        return 49.0, "2–4 business days"
    elif amt >= 500:
        return 79.0, "3–5 business days"
    else:
        return 99.0, "4–7 business days"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sector = models.CharField(max_length=50, default='Sector 1')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_days = models.CharField(max_length=60, default='4–7 business days')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'orders_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.order_id}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            last_order = Order.objects.order_by('-id').first()
            next_num = (last_order.id + 1) if last_order else 1
            self.order_id = f"QX-{next_num:04d}"
        super().save(*args, **kwargs)

    def get_item_count(self):
        return self.items.count()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'orders_orderitem'

    def get_subtotal(self):
        return self.price * self.quantity
