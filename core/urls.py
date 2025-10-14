# core/urls.py
from rest_framework import routers
from django.urls import path, include
from .views import accounts

router = routers.DefaultRouter()
router.register(r'organizations', accounts.OrganizationViewSet)
router.register(r'users', accounts.UserViewSet)
router.register(r'categories', accounts.CategoryViewSet)
router.register(r'products', accounts.ProductViewSet)
router.register(r'suppliers', accounts.SupplierViewSet)
router.register(r'customers', accounts.CustomerViewSet)
router.register(r'sales', accounts.SaleViewSet)
router.register(r'sale-items', accounts.SaleItemViewSet)
router.register(r'purchases', accounts.PurchaseViewSet)
router.register(r'purchase-items', accounts.PurchaseItemViewSet)
router.register(r'stock-movements', accounts.StockMovementViewSet)
router.register(r'contact-messages', accounts.ContactMessageViewSet)

urlpatterns = [
    # path("", include(router.urls)),
]


