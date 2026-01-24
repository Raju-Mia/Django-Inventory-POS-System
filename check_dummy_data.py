
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inventory_project.settings")
django.setup()

from core.models import Sale, Product

print("Checking for Dummy Data...")

# Check Sales
dummy_sales = Sale.objects.filter(invoice_number__in=["Invoice001", "Invoice002", "Invoice003"])
print(f"Found {dummy_sales.count()} dummy sales.")
for s in dummy_sales:
    print(f" - {s.invoice_number} (Customer: {s.customer})")

# Check Products
dummy_products = Product.objects.filter(product_id__in=["P001", "P002"])
print(f"Found {dummy_products.count()} dummy products.")
for p in dummy_products:
    print(f" - {p.product_id}: {p.name}")
