#  core/views.py

from rest_framework import viewsets, permissions
from accounts.models import Organization, CustomUser
from core.models import (
    Category, Product, Supplier, Customer, Sale, SaleItem, 
    Purchase, PurchaseItem, StockMovement, ContactMessage
)
from core.serializers.accounts import (
    OrganizationSerializer, UserSerializer, CategorySerializer, ProductSerializer,
    SupplierSerializer, CustomerSerializer, SaleSerializer, SaleItemSerializer,
    PurchaseSerializer, PurchaseItemSerializer, StockMovementSerializer, ContactMessageSerializer
)


# Base class for all organization-scoped models
class OrgModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]  # must be logged in

    def get_queryset(self):
        user = self.request.user
        # Ensure model has an 'organization' FK
        return self.queryset.filter(organization=user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


# ----------------------------
# VIEWSETS
# ----------------------------

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]  # only logged-in users


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users of the same organization only
        return self.queryset.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class CategoryViewSet(OrgModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(OrgModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class SupplierViewSet(OrgModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class CustomerViewSet(OrgModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class SaleViewSet(OrgModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer


class SaleItemViewSet(OrgModelViewSet):
    queryset = SaleItem.objects.all()
    serializer_class = SaleItemSerializer


class PurchaseViewSet(OrgModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer


class PurchaseItemViewSet(OrgModelViewSet):
    queryset = PurchaseItem.objects.all()
    serializer_class = PurchaseItemSerializer


class StockMovementViewSet(OrgModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer


class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]  # open to public
