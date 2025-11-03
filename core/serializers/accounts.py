from rest_framework import serializers
from accounts.models import Organization, CustomUser
from core.models import (
    Category, Product, Supplier, Customer,
    Sale, SaleItem, Purchase, PurchaseItem,
    StockMovement, ContactMessage
)

# -----------------------
# Organization & User
# -----------------------
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id","email","first_name","last_name","organization","role","is_owner","is_active")
        read_only_fields = ["organization"]  # auto-assigned from logged-in user

# -----------------------
# Core models
# -----------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["organization", "created_at"]

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["organization", "created_at", "updated_at"]



class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ["organization", "created_at", "updated_at"]

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ["organization", "created_at", "updated_at"]

# -----------------------
# Sale & SaleItem
# -----------------------
# class SaleItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SaleItem
#         fields = "__all__"
#         read_only_fields = ["sale", "subtotal"]

# class SaleSerializer(serializers.ModelSerializer):
#     items = SaleItemSerializer(many=True, read_only=True)

#     class Meta:
#         model = Sale
#         fields = "__all__"
#         read_only_fields = ["organization", "created_by", "created_at", "updated_at", "total_amount", "net_total"]


class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ("product", "quantity", "unit_price", "subtotal")
        read_only_fields = ("subtotal",)

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = "__all__"
        read_only_fields = ["organization", "created_by", "created_at", "updated_at", "total_amount", "net_total"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        user = self.context['request'].user

        # Create Sale
        sale = Sale.objects.create(
            created_by=user,
            **validated_data
        )

        total_amount = 0

        for item in items_data:
            product = item['product']
            quantity = item['quantity']
            unit_price = item.get('unit_price', product.sell_price)
            subtotal = quantity * unit_price

            # Create SaleItem
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )

            # Update total
            total_amount += subtotal

            # Create StockMovement (out)
            StockMovement.objects.create(
                organization=user.organization,
                product=product,
                movement_type="out",
                quantity=quantity,
                reference_number=sale.invoice_number,
                created_by=user
            )

            # Update product stock
            product.current_stock -= quantity
            product.save()

        sale.total_amount = total_amount
        sale.net_total = total_amount - sale.discount + sale.vat
        sale.save()

        return sale


# -----------------------
# Purchase & PurchaseItem
# -----------------------


class PurchaseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseItem
        fields = ("product", "quantity", "unit_price", "subtotal")
        read_only_fields = ("subtotal",)

class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True)

    class Meta:
        model = Purchase
        fields = "__all__"
        read_only_fields = ["organization", "created_by", "created_at", "updated_at", "total_amount"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        user = self.context['request'].user

        # Create Purchase
        purchase = Purchase.objects.create(
            created_by=user,
            **validated_data
        )

        total_amount = 0

        for item in items_data:
            product = item['product']
            quantity = item['quantity']
            unit_price = item.get('unit_price', product.purchase_price)
            subtotal = quantity * unit_price

            # Create PurchaseItem
            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            )

            # Update total
            total_amount += subtotal

            # Create StockMovement (in)
            StockMovement.objects.create(
                organization=user.organization,
                product=product,
                movement_type="in",
                quantity=quantity,
                reference_number=purchase.purchase_number,
                created_by=user
            )

            # Update product stock
            product.current_stock += quantity
            product.save()

        purchase.total_amount = total_amount
        purchase.save()

        return purchase


# -----------------------
# Stock Movement
# -----------------------
class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = "__all__"
        read_only_fields = ["organization", "created_by", "created_at"]

# -----------------------
# Contact Message
# -----------------------
class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"
        read_only_fields = ["created_at", "is_read"]
