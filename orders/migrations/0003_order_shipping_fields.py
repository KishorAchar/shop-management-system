from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_coupon_order_coupon_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipping_charge',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_days',
            field=models.CharField(default='4–7 business days', max_length=60),
        ),
    ]
