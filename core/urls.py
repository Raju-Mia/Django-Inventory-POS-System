# core/urls.py
from rest_framework import routers
from django.urls import path, include
from .views import all_view



router = routers.DefaultRouter()
# router.register(r'organizations', all_view.OrganizationViewSet)
# router.register(r'users', all_view.UserViewSet)
router.register(r'categories', all_view.CategoryViewSet)
router.register(r'products', all_view.ProductViewSet)
router.register(r'suppliers', all_view.SupplierViewSet)
router.register(r'customers', all_view.CustomerViewSet)
router.register(r'sales', all_view.SaleViewSet)
router.register(r'sale-items', all_view.SaleItemViewSet)
router.register(r'purchases', all_view.PurchaseViewSet)
router.register(r'purchase-items', all_view.PurchaseItemViewSet)
router.register(r'stock-movements', all_view.StockMovementViewSet)
router.register(r'contact-messages', all_view.ContactMessageViewSet)

urlpatterns = [
    path("", include(router.urls)),


    path('v1/invoices/<uuid:id>/pdf/', all_view.InvoicePDFDownloadAPIView.as_view(), name='invoice-pdf-download'),

    path("v1/reports/sales/", all_view.SalesReportAPIView.as_view(), name="sales-report"),
    path("v1/reports/stock/", all_view.StockReportAPIView.as_view(), name="stock-report"),

    path("v1/dashboard/inventory/", all_view.InventoryDashboardAPIView.as_view(), name="inventory-dashboard"),





]


