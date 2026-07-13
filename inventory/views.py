# inventory/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Q, Avg
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json

from .models import Product, StockMovement, ProductReview, WishlistItem
from orders.models import Order, OrderItem, Coupon
from accounts.models import User
from .utils import seed_mock_data
from orders.models import Coupon as CouponModel


@login_required
def command_center(request):
    if request.user.role == 'customer':
        return redirect('inventory:inventory_bay')

    total_sales = Order.objects.filter(status='completed').aggregate(total=Sum('total'))['total'] or 0
    total_orders = Order.objects.count()
    total_products = Product.objects.filter(is_active=True).count()
    total_customers = User.objects.filter(role='customer').count()

    target_sales = 100000
    sales_percentage = (float(total_sales) / target_sales) * 100 if target_sales > 0 else 0
    goal_achieved = total_sales >= target_sales
    capped_percentage = min(sales_percentage, 100)

    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
    low_stock = Product.objects.filter(stock__lt=10, is_active=True)[:3]

    # Recent reviews for admin
    recent_reviews = ProductReview.objects.select_related('product', 'customer').order_by('-created_at')[:5]
    pending_reviews = ProductReview.objects.filter(is_approved=False).count()

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_customers': total_customers,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'target_sales': target_sales,
        'sales_percentage': sales_percentage,
        'capped_percentage': capped_percentage,
        'goal_achieved': goal_achieved,
        'recent_reviews': recent_reviews,
        'pending_reviews': pending_reviews,
    }
    return render(request, 'dashboard/command_center.html', context)


@login_required
def inventory_bay(request):
    # Auto-refresh bestseller badge: top product by total qty sold
    top_product = (
        OrderItem.objects
        .values('product')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')
        .first()
    )
    if top_product:
        Product.objects.all().update(is_bestseller=False)
        Product.objects.filter(id=top_product['product']).update(is_bestseller=True)
    else:
        # If no orders yet, mark highest-priced product as bestseller as a placeholder
        top_by_price = Product.objects.filter(is_active=True).order_by('-price').first()
        if top_by_price:
            Product.objects.all().update(is_bestseller=False)
            top_by_price.is_bestseller = True
            top_by_price.save()

    products = Product.objects.filter(is_active=True)

    category = request.GET.get('category')
    if category and category != 'all':
        products = products.filter(category=category)

    search = request.GET.get('search')
    if search:
        products = products.filter(Q(name__icontains=search) | Q(sku__icontains=search))

    categories = Product.CATEGORY_CHOICES

    # AI Recommendations: products in same category as past orders
    recommended = []
    if request.user.is_authenticated:
        past_categories = OrderItem.objects.filter(
            order__customer=request.user
        ).values_list('product__category', flat=True).distinct()

        if past_categories:
            already_bought = OrderItem.objects.filter(
                order__customer=request.user
            ).values_list('product_id', flat=True).distinct()
            recommended = list(
                Product.objects
                .filter(is_active=True, category__in=past_categories)
                .exclude(id__in=already_bought)
                .annotate(total_sold=Sum('orderitem__quantity'))
                .order_by('-total_sold')[:6]
            )

        if not recommended:
            # Fallback: top sellers overall
            recommended = list(
                Product.objects
                .filter(is_active=True)
                .annotate(total_sold=Sum('orderitem__quantity'))
                .order_by('-total_sold')[:6]
            )

    available_coupons = CouponModel.objects.filter(is_active=True).order_by('code')

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category or 'all',
        'recommended': recommended,
        'available_coupons': available_coupons,
    }
    return render(request, 'dashboard/inventory.html', context)


@login_required
def add_product(request):
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    if request.method == 'POST':
        product = Product.objects.create(
            name=request.POST.get('name'),
            price=request.POST.get('price'),
            stock=request.POST.get('stock'),
            category=request.POST.get('category'),
            sku=request.POST.get('sku'),
            icon=request.POST.get('icon', '📦'),
            created_by=request.user
        )
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
        return JsonResponse({'success': True, 'product_id': product.id})
    return JsonResponse({'success': False})


@login_required
def edit_product(request, product_id):
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name     = request.POST.get('name')
        product.price    = request.POST.get('price')
        product.category = request.POST.get('category')
        product.sku      = request.POST.get('sku')
        product.icon     = request.POST.get('icon', '📦')
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'category': product.category,
                'sku': product.sku,
                'icon': product.icon,
                'image_url': product.image.url if product.image else '',
            }
        })
    return JsonResponse({'success': False})


@login_required
def update_stock(request, product_id):
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        new_stock = int(request.POST.get('stock', 0))
        StockMovement.objects.create(
            product=product,
            quantity=new_stock - product.stock,
            movement_type='adjust',
            created_by=request.user,
            notes='Manual adjustment'
        )
        product.stock = new_stock
        product.save()
        return JsonResponse({'success': True, 'new_stock': product.stock})
    return JsonResponse({'success': False})


@login_required
def systems(request):
    if request.user.role == 'customer':
        return redirect('inventory:inventory_bay')
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'dashboard/systems.html', {'coupons': coupons})


@login_required
def update_settings(request):
    if request.method == 'POST':
        user = request.user
        dark_theme = request.POST.get('dark_theme') == 'true'
        user.dark_theme = dark_theme
        user.save()
        messages.success(request, f'Settings updated. {"Dark mode" if dark_theme else "Light mode"} engaged.')
        return redirect('inventory:systems')
    return redirect('inventory:systems')


def dashboard_view(request):
    seed_mock_data()
    products = Product.objects.all()
    return render(request, 'inventory/dashboard.html', {'products': products})


# ─── Reviews ─────────────────────────────────────────────────────────────────

@login_required
def submit_review(request, product_id):
    """Customer submits a review for a product."""
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.method == 'POST':
        if request.user.role != 'customer':
            return JsonResponse({'success': False, 'error': 'Only customers can submit reviews.'})

        rating = request.POST.get('rating')
        title = request.POST.get('title', '')
        body = request.POST.get('body', '')

        if not rating or not body:
            return JsonResponse({'success': False, 'error': 'Rating and review text are required.'})

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise ValueError()
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid rating value.'})

        review, created = ProductReview.objects.update_or_create(
            product=product,
            customer=request.user,
            defaults={'rating': rating, 'title': title, 'body': body, 'is_approved': True}
        )

        avg = product.get_average_rating()
        return JsonResponse({
            'success': True,
            'message': 'Review submitted successfully!',
            'review': {
                'username': request.user.username,
                'rating': rating,
                'title': title,
                'body': body,
                'created': 'Just now',
            },
            'new_avg': avg,
            'review_count': product.get_review_count(),
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
def product_reviews(request, product_id):
    """Admin: list reviews for a product."""
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.select_related('customer').order_by('-created_at')
    return JsonResponse({
        'product': product.name,
        'avg_rating': product.get_average_rating(),
        'reviews': [
            {
                'id': r.id,
                'customer': r.customer.username,
                'rating': r.rating,
                'title': r.title,
                'body': r.body,
                'is_approved': r.is_approved,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for r in reviews
        ]
    })


@login_required
def moderate_review(request, review_id):
    """Admin: approve or delete a review."""
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    review = get_object_or_404(ProductReview, id=review_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            review.is_approved = True
            review.save()
            return JsonResponse({'success': True, 'message': 'Review approved.'})
        elif action == 'delete':
            review.delete()
            return JsonResponse({'success': True, 'message': 'Review deleted.'})

    return JsonResponse({'success': False, 'error': 'Invalid action.'})


@login_required
def all_reviews(request):
    """Admin: all reviews dashboard view."""
    if request.user.role == 'customer':
        return redirect('inventory:inventory_bay')

    reviews = ProductReview.objects.select_related('product', 'customer').order_by('-created_at')
    context = {'reviews': reviews}
    return render(request, 'dashboard/reviews.html', context)


# ─── Coupons ──────────────────────────────────────────────────────────────────

@login_required
def manage_coupons(request):
    """Admin: list all coupons and handle create/delete."""
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            import decimal
            from datetime import datetime as dt

            code = request.POST.get('code', '').strip().upper()
            discount_type = request.POST.get('discount_type', 'percentage')
            discount_value_raw = request.POST.get('discount_value', '').strip()
            min_order_raw = request.POST.get('min_order_amount', '').strip()
            max_uses_raw = request.POST.get('max_uses', '').strip()
            valid_from_raw = request.POST.get('valid_from', '').strip()
            valid_to_raw = request.POST.get('valid_to', '').strip()

            if not code or not discount_value_raw:
                messages.error(request, 'Code and discount value are required.')
                return redirect('/dashboard/systems/?tab=coupons')

            if Coupon.objects.filter(code=code).exists():
                messages.error(request, f'Coupon code "{code}" already exists.')
                return redirect('/dashboard/systems/?tab=coupons')

            def parse_dt(raw):
                if not raw or not raw.strip():
                    return None
                import datetime as _dt
                import zoneinfo
                from django.utils import timezone as tz
                for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M'):
                    try:
                        naive = _dt.datetime.strptime(raw.strip(), fmt)
                        try:
                            return tz.make_aware(naive)
                        except Exception:
                            return naive.replace(tzinfo=_dt.timezone.utc)
                    except (ValueError, TypeError):
                        continue
                return None

            try:
                discount_value = decimal.Decimal(discount_value_raw)
                min_order_amount = decimal.Decimal(min_order_raw) if min_order_raw else decimal.Decimal('0')
                max_uses = int(max_uses_raw) if max_uses_raw else 100
                valid_from = parse_dt(valid_from_raw) or timezone.now()
                valid_to = parse_dt(valid_to_raw)

                Coupon.objects.create(
                    code=code,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    min_order_amount=min_order_amount,
                    max_uses=max_uses,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    is_active=True,
                    created_by=request.user,
                )
                messages.success(request, f'Coupon "{code}" created successfully!')
            except Exception as e:
                messages.error(request, f'Error creating coupon: {str(e)}')
            return redirect('/dashboard/systems/?tab=coupons')

        elif action == 'delete':
            coupon_id = request.POST.get('coupon_id')
            coupon = get_object_or_404(Coupon, id=coupon_id)
            coupon.delete()
            messages.success(request, 'Coupon deleted.')
            return redirect('/dashboard/systems/?tab=coupons')

        elif action == 'toggle':
            coupon_id = request.POST.get('coupon_id')
            coupon = get_object_or_404(Coupon, id=coupon_id)
            coupon.is_active = not coupon.is_active
            coupon.save()
            return JsonResponse({'success': True, 'is_active': coupon.is_active})

    return redirect('/dashboard/systems/?tab=coupons')


@login_required
def delete_product(request, product_id):
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def wishlist_page(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'dashboard/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()
            return JsonResponse({'success': True, 'wishlisted': False})
        return JsonResponse({'success': True, 'wishlisted': True})
    return JsonResponse({'success': False})
