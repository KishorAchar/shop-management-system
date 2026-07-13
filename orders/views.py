# orders/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
import json

from .models import Order, OrderItem, Coupon, calculate_shipping
from inventory.models import Product


@login_required
def orbital_orders(request):
    if request.user.role == 'customer':
        orders = Order.objects.filter(customer=request.user)
    else:
        orders = Order.objects.select_related('customer').all()

    status = request.GET.get('status')
    if status and status != 'all':
        orders = orders.filter(status=status)

    products_list = [
        {
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'icon': p.icon
        }
        for p in Product.objects.filter(is_active=True)
    ]

    context = {
        'orders': orders,
        'statuses': Order.STATUS_CHOICES,
        'products_list': products_list,
        'categories': Product.CATEGORY_CHOICES,
        'selected_status': status or 'all',
    }
    return render(request, 'dashboard/orbital_orders.html', context)


@login_required
def order_detail(request, order_id):
    if request.user.role == 'customer':
        order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    else:
        order = get_object_or_404(Order, order_id=order_id)

    return render(request, 'dashboard/order_detail.html', {'order': order})


@login_required
def update_status(request, order_id):
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    order = get_object_or_404(Order, order_id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        old_status = order.status
        valid_statuses = [s[0] for s in Order.STATUS_CHOICES]

        if new_status in valid_statuses:
            with transaction.atomic():
                if new_status == 'cancelled' and old_status != 'cancelled':
                    for item in order.items.all():
                        product = Product.objects.select_for_update().get(id=item.product.id)
                        product.stock += item.quantity
                        product.save()
                elif old_status == 'cancelled' and new_status != 'cancelled':
                    for item in order.items.all():
                        product = Product.objects.select_for_update().get(id=item.product.id)
                        if product.stock < item.quantity:
                            return JsonResponse({'success': False, 'error': f'Insufficient stock for {product.name}'})
                        product.stock -= item.quantity
                        product.save()

                order.status = new_status
                order.save()

            return JsonResponse({'success': True, 'status': new_status})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def delete_order(request, order_id):
    if request.user.role == 'customer':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})

    order = get_object_or_404(Order, order_id=order_id)

    if request.method == 'POST':
        with transaction.atomic():
            if order.status != 'cancelled':
                for item in order.items.all():
                    product = Product.objects.select_for_update().get(id=item.product.id)
                    product.stock += item.quantity
                    product.save()
            order.delete()

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})


@login_required
def validate_coupon(request):
    """AJAX endpoint to validate coupon and return discount info."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    try:
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        code = data.get('code', '').strip().upper()
        order_total = float(data.get('order_total', 0) or 0)

        if not code:
            return JsonResponse({'success': False, 'error': 'Please enter a coupon code.'})

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid coupon code.'})

        valid, msg = coupon.is_valid()
        if not valid:
            return JsonResponse({'success': False, 'error': msg})

        if order_total < float(coupon.min_order_amount):
            return JsonResponse({
                'success': False,
                'error': f'Minimum order ₹{coupon.min_order_amount} required for this coupon.'
            })

        discount = float(coupon.calculate_discount(order_total))
        final_after_discount = order_total - discount
        shipping_charge, delivery_days = calculate_shipping(final_after_discount)
        final_total = final_after_discount + shipping_charge

        return JsonResponse({
            'success': True,
            'coupon_id': coupon.id,
            'code': coupon.code,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'discount_amount': discount,
            'shipping_charge': shipping_charge,
            'delivery_days': delivery_days,
            'final_total': round(final_total, 2),
            'message': f'Coupon applied! You save ₹{discount:.2f}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
def create_order(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        sector = request.POST.get('sector', 'Sector 1')
        coupon_code = request.POST.get('coupon_code', '').strip().upper()

        if not product_ids:
            return JsonResponse({'success': False, 'error': 'No items selected'})

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    customer=request.user,
                    sector=sector,
                    total=0,
                    original_total=0,
                    status='pending'
                )

                running_total = 0
                items_added = 0

                for p_id, qty_str in zip(product_ids, quantities):
                    qty = int(qty_str)
                    if qty <= 0:
                        raise ValueError("Quantity must be at least 1")

                    product = Product.objects.select_for_update().get(id=p_id)

                    if product.stock < qty:
                        raise ValueError(f"Insufficient stock for {product.name}")

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price=product.price
                    )

                    product.stock -= qty
                    product.save()

                    running_total += product.price * qty
                    items_added += 1

                if items_added == 0:
                    raise ValueError("No valid items")

                from decimal import Decimal
                order.original_total = running_total
                discount_amount = Decimal('0')
                applied_coupon = None

                # Apply coupon if provided
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)
                        valid, msg = coupon.is_valid()
                        if valid and running_total >= coupon.min_order_amount:
                            discount_amount = coupon.calculate_discount(running_total)
                            applied_coupon = coupon
                            coupon.used_count += 1
                            coupon.save()
                    except Coupon.DoesNotExist:
                        pass

                order.coupon = applied_coupon
                order.discount_amount = discount_amount
                after_discount = running_total - discount_amount
                shipping_charge_float, delivery_days = calculate_shipping(after_discount)
                shipping_charge = Decimal(str(shipping_charge_float))
                order.shipping_charge = shipping_charge
                order.delivery_days = delivery_days
                order.total = after_discount + shipping_charge
                order.save()

                # Update bestseller: top product by total qty sold
                from django.db.models import Sum as DSum
                top_product = (
                    OrderItem.objects
                    .values('product')
                    .annotate(total_sold=DSum('quantity'))
                    .order_by('-total_sold')
                    .first()
                )
                if top_product:
                    Product.objects.all().update(is_bestseller=False)
                    Product.objects.filter(id=top_product['product']).update(is_bestseller=True)

                return JsonResponse({
                    'success': True,
                    'order_id': order.order_id,
                    'total': str(order.total),
                    'original_total': str(order.original_total),
                    'discount_amount': str(order.discount_amount),
                    'shipping_charge': str(order.shipping_charge),
                    'delivery_days': order.delivery_days,
                    'coupon_applied': applied_coupon.code if applied_coupon else None,
                })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def download_invoice(request, order_id):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    import io

    if request.user.role == 'customer':
        order = get_object_or_404(Order, order_id=order_id, customer=request.user)
    else:
        order = get_object_or_404(Order, order_id=order_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    accent = colors.HexColor('#7c3aed')
    dark = colors.HexColor('#1e1b4b')
    grey = colors.HexColor('#6b7280')

    title_style = ParagraphStyle('title', fontSize=28, textColor=accent, fontName='Helvetica-Bold', spaceAfter=4)
    sub_style   = ParagraphStyle('sub',   fontSize=10, textColor=grey,   fontName='Helvetica')
    label_style = ParagraphStyle('lbl',   fontSize=9,  textColor=grey,   fontName='Helvetica')
    value_style = ParagraphStyle('val',   fontSize=10, textColor=dark,   fontName='Helvetica-Bold')
    right_style = ParagraphStyle('right', fontSize=11, textColor=dark,   fontName='Helvetica-Bold', alignment=TA_RIGHT)
    total_style = ParagraphStyle('tot',   fontSize=16, textColor=accent, fontName='Helvetica-Bold', alignment=TA_RIGHT)

    elements = []

    # Header
    elements.append(Paragraph("JK SHOP", title_style))
    elements.append(Paragraph("Your trusted marketplace", sub_style))
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=accent))
    elements.append(Spacer(1, 4*mm))

    # Order meta table
    meta_data = [
        [Paragraph("INVOICE", ParagraphStyle('inv', fontSize=20, textColor=dark, fontName='Helvetica-Bold')),
         Paragraph(f"Order #<b>{order.order_id}</b>", right_style)],
        [Paragraph("JK Shop Pvt. Ltd.", label_style),
         Paragraph(f"Date: {order.created_at.strftime('%d %b %Y')}", right_style)],
        [Paragraph("Bangalore, Karnataka, India", label_style),
         Paragraph(f"Status: <b>{order.get_status_display()}</b>", right_style)],
        [Paragraph("jkshop@example.com", label_style),
         Paragraph(f"Sector: {order.sector}", right_style)],
    ]
    meta_table = Table(meta_data, colWidths=[90*mm, 90*mm])
    meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 3)]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6*mm))

    # Bill to
    elements.append(Paragraph("BILL TO", label_style))
    elements.append(Paragraph(f"<b>{order.customer.username}</b>", value_style))
    elements.append(Paragraph(order.customer.email or "—", sub_style))
    elements.append(Spacer(1, 5*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 4*mm))

    # Items table
    header_row = [
        Paragraph('<b>#</b>', ParagraphStyle('th', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph('<b>PRODUCT</b>', ParagraphStyle('th', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')),
        Paragraph('<b>UNIT PRICE</b>', ParagraphStyle('th', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('<b>QTY</b>', ParagraphStyle('th', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('<b>SUBTOTAL</b>', ParagraphStyle('th', fontSize=9, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]
    rows = [header_row]
    for i, item in enumerate(order.items.all(), 1):
        row = [
            Paragraph(str(i), sub_style),
            Paragraph(f"{item.product.icon} {item.product.name}", value_style),
            Paragraph(f"₹{item.price}", ParagraphStyle('r', fontSize=10, alignment=TA_RIGHT)),
            Paragraph(str(item.quantity), ParagraphStyle('c', fontSize=10, alignment=TA_CENTER)),
            Paragraph(f"₹{item.get_subtotal()}", ParagraphStyle('rb', fontSize=10, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ]
        rows.append(row)

    items_table = Table(rows, colWidths=[10*mm, 75*mm, 35*mm, 20*mm, 40*mm])
    ts = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), accent),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f9fafb'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])
    items_table.setStyle(ts)
    elements.append(items_table)
    elements.append(Spacer(1, 5*mm))

    # Totals
    totals = []
    if order.discount_amount > 0:
        totals.append(['Subtotal', f"₹{order.original_total}"])
        totals.append([f"Discount ({order.coupon.code if order.coupon else 'Coupon'})", f"-₹{order.discount_amount}"])
    else:
        totals.append(['Subtotal', f"₹{order.original_total}"])
    if order.shipping_charge > 0:
        totals.append(['Shipping & Delivery', f"₹{order.shipping_charge}"])
    else:
        totals.append(['Shipping & Delivery', "FREE"])
    totals.append([f'Estimated Delivery', order.delivery_days])
    totals.append(['TOTAL', f"₹{order.total}"])

    totals_table = Table(
        [[Paragraph(r[0], ParagraphStyle('tl', fontSize=10, textColor=grey if r[0]!='TOTAL' else accent, fontName='Helvetica-Bold' if r[0]=='TOTAL' else 'Helvetica', alignment=TA_RIGHT)),
          Paragraph(r[1], ParagraphStyle('tr', fontSize=10 if r[0]!='TOTAL' else 16, textColor=dark if r[0]!='TOTAL' else accent, fontName='Helvetica-Bold', alignment=TA_RIGHT))]
         for r in totals],
        colWidths=[130*mm, 50*mm]
    )
    totals_table.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    elements.append(totals_table)
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("Thank you for shopping with JK Shop!", ParagraphStyle('foot', fontSize=10, textColor=grey, alignment=TA_CENTER)))

    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="JKShop_Invoice_{order.order_id}.pdf"'
    return response
