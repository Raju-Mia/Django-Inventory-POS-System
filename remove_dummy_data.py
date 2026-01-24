
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
django.setup()

from core.models import Sale, Product, SaleItem, StockMovement


print("Removing Dummy Data...")

# 1. Identify Dummy Products
dummy_products = Product.objects.filter(product_id__in=["P001", "P002"])
product_ids = list(dummy_products.values_list('id', flat=True))

# 2. Identify Dummy Sales
dummy_sales = Sale.objects.filter(invoice_number__in=["Invoice001", "Invoice002", "Invoice003"])
sale_ids = list(dummy_sales.values_list('id', flat=True))

# 3. Delete dependent SaleItems
# Delete by Sale
items_by_sale = SaleItem.objects.filter(sale__id__in=sale_ids)
print(f"Deleting {items_by_sale.count()} SaleItems by Sale ID...")
items_by_sale.delete()

# Delete by Product (orphaned or in other sales)
items_by_product = SaleItem.objects.filter(product__id__in=product_ids)
print(f"Deleting {items_by_product.count()} SaleItems by Product ID...")
items_by_product.delete()

# 4. Delete dependent PurchaseItems (CRITICAL: Product deletion might be blocked by these)
# Need to import PurchaseItem first
from core.models import PurchaseItem
purchase_items = PurchaseItem.objects.filter(product__id__in=product_ids)
print(f"Deleting {purchase_items.count()} PurchaseItems...")
purchase_items.delete()

# 5. Delete dependent StockMovements
movements_to_delete = StockMovement.objects.filter(product__id__in=product_ids)
print(f"Deleting {movements_to_delete.count()} StockMovements...")
movements_to_delete.delete()

# 6. Delete Sales
count_sales = dummy_sales.count()
if count_sales > 0:
    print(f"Deleting {count_sales} dummy sales...")
    dummy_sales.delete()
else:
    print("No dummy sales found.")

# 7. Delete Products
count_products = dummy_products.count()
if count_products > 0:
    print(f"Deleting {count_products} dummy products...")
    dummy_products.delete()
else:
    print("No dummy products found.")

print("Cleanup Complete!")
