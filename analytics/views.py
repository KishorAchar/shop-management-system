from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from orders.models import Order, OrderItem
from inventory.models import Product
from accounts.models import User


@login_required
def data_core(request):
    # Total orders and revenue
    completed_orders = Order.objects.filter(status='completed')
    total_orders = Order.objects.count()
    total_revenue = completed_orders.aggregate(total=Sum('total'))['total'] or 0

    # Conversion rate: completed orders / all orders
    conversion_rate = round((completed_orders.count() / total_orders * 100), 1) if total_orders > 0 else 0

    # Average order value
    avg_order_value = (total_revenue / completed_orders.count()) if completed_orders.count() > 0 else 0

    # Customer retention: customers with more than 1 order
    total_customers = User.objects.filter(role='customer').count()
    repeat_customers = (
        Order.objects.values('customer')
        .annotate(order_count=Count('id'))
        .filter(order_count__gt=1)
        .count()
    )
    retention_rate = round((repeat_customers / total_customers * 100), 1) if total_customers > 0 else 0

    # Top products by quantity sold
    top_products = (
        OrderItem.objects.values('product__name', 'product__price')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )
    top_products_list = [
        {'name': item['product__name'], 'price': item['product__price'], 'order_count': item['total_sold']}
        for item in top_products
    ]

    # Revenue data for the last 7 days with pre-calculated bar height
    today = timezone.now().date()
    raw_revenue = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_revenue = (
            Order.objects.filter(status='completed', created_at__date=day)
            .aggregate(total=Sum('total'))['total'] or 0
        )
        raw_revenue.append({'day': day.strftime('%a'), 'revenue': float(day_revenue)})

    max_revenue = max((d['revenue'] for d in raw_revenue), default=1) or 1
    revenue_data = [
        {**d, 'bar_height': round(d['revenue'] / max_revenue * 200) if d['revenue'] else 5}
        for d in raw_revenue
    ]

    context = {
        'conversion_rate': conversion_rate,
        'avg_order_value': avg_order_value,
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'retention_rate': retention_rate,
        'top_products': top_products_list,
        'revenue_data': revenue_data,
    }
    return render(request, 'dashboard/analytics.html', context)
