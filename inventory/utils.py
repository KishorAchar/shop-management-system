# inventory/utils.py
from .models import Product, StockMovement
from accounts.models import User
import random

def seed_mock_data():
    if Product.objects.exists(): return  # Don't add data if already exists
    
    # Assuming at least one user exists
    user = User.objects.first() 
    
    categories = ['electronics', 'drones', 'wearables']
    for i in range(10):
        p = Product.objects.create(
            name=f"Mock Product {i}",
            price=random.uniform(10.0, 500.0),
            stock=random.randint(0, 100),
            category=random.choice(categories),
            sku=f"SKU-{i}",
            created_by=user
        )
        
        # Add a few movements for each product
        for _ in range(3):
            StockMovement.objects.create(
                product=p,
                quantity=random.randint(-10, 20),
                movement_type='in',
                created_by=user
            )