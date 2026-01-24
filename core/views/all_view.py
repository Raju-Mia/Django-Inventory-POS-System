#  core/views.py
import io
from decimal import Decimal
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
import os
from django.templatetags.static import static
PDF_STORAGE_PATH = os.path.join("media", "invoices")
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta


from django.db.models import Sum, F, Q
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated  # adjust as you like
from weasyprint import HTML, CSS



from rest_framework import viewsets, permissions
from accounts.models import Organization, CustomUser
from core.models import (
    Category, Product, Supplier, Customer, Sale, SaleItem, 
    Purchase, PurchaseItem, StockMovement, ContactMessage
)
from core.serializers.all_serializers import (
    OrganizationSerializer, UserSerializer, CategorySerializer, ProductSerializer,
    SupplierSerializer, CustomerSerializer, SaleSerializer, SaleItemSerializer,
    PurchaseSerializer, PurchaseItemSerializer, StockMovementSerializer, ContactMessageSerializer, SaleSummarySerializer, ProductStockSerializer
)


from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDate, TruncMonth
from datetime import timedelta
from django.utils import timezone


from core.permissions import RolePermission



# Base class for all organization-scoped models
class OrgModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, RolePermission]  # must be logged in

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
    permission_classes = [permissions.IsAuthenticated, RolePermission]  # only logged-in users


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RolePermission]

    def get_queryset(self):
        # Users of the same organization only
        return self.queryset.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)




class CategoryViewSet(OrgModelViewSet):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)



class ProductViewSet(OrgModelViewSet):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        return Product.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class SupplierViewSet(OrgModelViewSet):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    serializer_class = SupplierSerializer
    
    def get_queryset(self):
        return Supplier.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class CustomerViewSet(OrgModelViewSet):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    serializer_class = CustomerSerializer
    
    def get_queryset(self):
        return Customer.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class SaleViewSet(OrgModelViewSet):
    permission_classes = [permissions.IsAuthenticated, RolePermission]
    serializer_class = SaleSerializer
    
    def get_queryset(self):
        return Sale.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class SaleItemViewSet(OrgModelViewSet):
    queryset = SaleItem.objects.all()
    serializer_class = SaleItemSerializer


class PurchaseViewSet(OrgModelViewSet):
    serializer_class = PurchaseSerializer
    
    def get_queryset(self):
        return Purchase.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


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

    def perform_create(self, serializer):
        instance = serializer.save()
        # Send email notification
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"New Contact Message from {instance.name}: {instance.subject}"
        body = f"""
You have received a new contact message.

Name: {instance.name}
Email: {instance.email}
Subject: {instance.subject}

Message:
{instance.message}
        """
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                ['nazmultec1011@gmail.com'],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send contact email: {e}")







# ============  Custom View ========
class InvoicePDFDownloadAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # enable if you want auth

    def get(self, request, id):
        """Generates and returns the PDF for a Sale invoice."""
        print("========== Generating Invoice ==========")

        # 1️⃣ Get the Sale record (invoice)
        # Ensure the user can only download their organization's invoices
        invoice = get_object_or_404(Sale, id=id)
        
        # Security Check:
        if request.user.is_authenticated and invoice.organization != request.user.organization:
             # If not authenticated or org mismatch (though is_authenticated checked in permission_classes if set)
             # But here we are explicit. If we want to support public download links without auth, 
             # we'd need a different strategy (e.g. signed URLs). 
             # Assuming this is an internal protected endpoint:
             return HttpResponse("Unauthorized Access to this Invoice", status=403)

        # 2️⃣ Prepare HTML content
        html_string = render_to_string('invoices/invoice.html', {
            'sale': invoice,
            'org': invoice.organization,
            'customer': invoice.customer,
        })

        # 3️⃣ Ensure directory exists
        os.makedirs(PDF_STORAGE_PATH, exist_ok=True)

        # 4️⃣ Generate PDF and save
        pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_file_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)

        HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(pdf_file_path)

        # 5️⃣ Serve the PDF for download
        with open(pdf_file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            return response





# ============  SalesReportAPIView  ========

class SalesReportAPIView(APIView):
    permission_classes = [IsAuthenticated]  # optional

    def get(self, request):
        user = request.user
        # ---- Filters ----
        start_date = request.query_params.get("from")
        end_date = request.query_params.get("to")
        search = request.query_params.get("search")

        sales = Sale.objects.filter(organization=user.organization).select_related("customer", "organization").prefetch_related("items")

        if start_date:
            sales = sales.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            sales = sales.filter(created_at__date__lte=parse_date(end_date))

        if search:
            sales = sales.filter(
                Q(invoice_number__icontains=search)
                | Q(customer__name__icontains=search)
            )

        # ---- Totals ----
        invoices_count = sales.count()
        total_items_sold = (
            SaleItem.objects.filter(sale__in=sales).aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        total_revenue = (
            sales.aggregate(total=Sum("net_total"))["total"] or 0
        )
        total_discount = (
            sales.aggregate(total=Sum("discount"))["total"] or 0
        )

        # ---- Serialize invoice list ----
        serializer = SaleSummarySerializer(sales, many=True)

        data = {
            "summary": {
                "organization": user.organization.name if user.organization else "",
                "invoices": invoices_count,
                "items_sold": total_items_sold,
                "revenue": float(total_revenue),
                "discounts": float(total_discount),
            },
            "sales": serializer.data,
        }
        return Response(data)



# ============  StockReportAPIView  ========


class StockReportAPIView(APIView):
    permission_classes = [IsAuthenticated]  # optional

    def get(self, request):
        user = request.user
        search = request.query_params.get("search")

        # ---- Filter products ----
        products = Product.objects.filter(organization=user.organization).select_related("category", "organization").all()

        if search:
            products = products.filter(
                Q(name__icontains=search)
                | Q(sku__icontains=search)
                | Q(product_id__icontains=search)
            )

        # ---- Aggregates ----
        stock_value_cost = (
            products.aggregate(
                total=Sum(F("purchase_price") * F("current_stock"))
            )["total"]
            or 0
        )
        stock_value_retail = (
            products.aggregate(
                total=Sum(F("sell_price") * F("current_stock"))
            )["total"]
            or 0
        )
        low_stock_count = products.filter(current_stock__lte=F("reorder_level")).count()
        out_of_stock_count = products.filter(current_stock__lte=0).count()

        # ---- Serialize detailed product list ----
        serializer = ProductStockSerializer(products, many=True)

        data = {
            "summary": {
                "organization": user.organization.name if user.organization else "",
                "stock_value_cost": float(stock_value_cost),
                "stock_value_retail": float(stock_value_retail),
                "low_stock_items": low_stock_count,
                "out_of_stock_items": out_of_stock_count,
            },
            "products": serializer.data,
        }
        return Response(data)



# ===========  InventoryDashboardAPIView  ========

class InventoryDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        org = user.organization
        now = timezone.now()
        seven_days_ago = now - timedelta(days=6)

        # 1️⃣ Basic Stats
        total_products = Product.objects.filter(organization=org).count()
        total_suppliers = Supplier.objects.filter(organization=org).count()
        low_stock_items = Product.objects.filter(
            organization=org, current_stock__lte=F("reorder_level")
        ).count()

        total_stock_value_cost = (
            Product.objects.filter(organization=org)
            .aggregate(total=Sum(F("purchase_price") * F("current_stock")))["total"]
            or 0
        )

        total_stock_value_retail = (
            Product.objects.filter(organization=org)
            .aggregate(total=Sum(F("sell_price") * F("current_stock")))["total"]
            or 0
        )

        # 2️⃣ Stock Value by Month (last 6 months)
        stock_by_month = (
            Product.objects.filter(organization=org)
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total_value=Sum(F("purchase_price") * F("current_stock")))
            .order_by("month")
        )

        stock_value_chart = [
            {"month": item["month"].strftime("%b"),
             "value": float(item["total_value"] or 0)}
            for item in stock_by_month
        ]

        # 3️⃣ Sales Trend (last 7 days)
        sales_trend = (
            Sale.objects.filter(organization=org, created_at__date__gte=seven_days_ago)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total_sales=Sum("net_total"))
            .order_by("day")
        )

        sales_chart = [
            {"day": str(item["day"]), "sales": float(item["total_sales"] or 0)}
            for item in sales_trend
        ]

        # 4️⃣ Category Distribution
        category_distribution = (
            Product.objects.filter(organization=org)
            .values("category__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        category_chart = [
            {"category": item["category__name"] or "Uncategorized", "count": item["count"]}
            for item in category_distribution
        ]

        # 5️⃣ Top 5 Products Sold
        top_products = (
            SaleItem.objects.filter(sale__organization=org)
            .values("product__name", "product__category__name")
            .annotate(total_sold=Sum("quantity"),
                      total_sales=Sum("subtotal"))
            .order_by("-total_sold")[:5]
        )

        top_sold_list = [
            {
                "name": item["product__name"],
                "category": item["product__category__name"],
                "quantity_sold": item["total_sold"],
                "sales_value": float(item["total_sales"] or 0),
            }
            for item in top_products
        ]

        # 📦 Final JSON Response
        data = {
            "summary": {
                "organization": org.name if org else "",
                "total_products": total_products,
                "total_suppliers": total_suppliers,
                "low_stock_items": low_stock_items,
                "total_stock_value_cost": float(total_stock_value_cost),
                "total_stock_value_retail": float(total_stock_value_retail),
            },
            "charts": {
                "stock_value_by_month": stock_value_chart,
                "sales_trend_last_7_days": sales_chart,
                "category_distribution": category_chart,
            },
            "top_products_sold": top_sold_list,
        }

        return Response(data)





# class InventoryDashboardAPIView(APIView):
#     permission_classes = [IsAuthenticated]  # optional

#     def get(self, request):
#         user = request.user
#         now = timezone.now()
#         seven_days_ago = now - timedelta(days=6)

#         # 1️⃣ Basic Stats
#         total_products = Product.objects.filter(organization=user.organization).count()
#         total_suppliers = Supplier.objects.filter(organization=user.organization).count()
#         low_stock_items = Product.objects.filter(current_stock__lte=F("reorder_level"), organization=user.organization).count()

#         total_stock_value_cost = (
#             Product.objects.aggregate(
#                 total=Sum(F("purchase_price") * F("current_stock"))
#             )["total"]
#             or 0
#         )

#         total_stock_value_retail = (
#             Product.objects.aggregate(
#                 total=Sum(F("sell_price") * F("current_stock")),
#             )["total"]
#             or 0
#         )


#         # 2️⃣ Stock Value by Month (last 6 months)
#         stock_by_month = (
#             Product.objects.annotate(month=TruncMonth("created_at"))
#             .values("month")
#             .annotate(total_value=Sum(F("purchase_price") * F("current_stock")))
#             .order_by("month")
#         )

#         stock_value_chart = [
#             {"month": item["month"].strftime("%b"), "value": float(item["total_value"] or 0)}
#             for item in stock_by_month
#         ]

#         # 3️⃣ Sales Trend (last 7 days)
#         sales_trend = (
#             Sale.objects.filter(created_at__date__gte=seven_days_ago)
#             .annotate(day=F("created_at__date"))
#             .values("day")
#             .annotate(total_sales=Sum("net_total"))
#             .order_by("day")
#         )
#         sales_chart = [
#             {"day": str(item["day"]), "sales": float(item["total_sales"] or 0)}
#             for item in sales_trend
#         ]

#         # 4️⃣ Product Category Distribution
#         category_distribution = (
#             Product.objects.values("category__name")
#             .annotate(count=Count("id"))
#             .order_by("-count")
#         )
#         category_chart = [
#             {"category": item["category__name"] or "Uncategorized", "count": item["count"]}
#             for item in category_distribution
#         ]

#         # 5️⃣ Top 5 Products Sold
#         top_products = (
#             SaleItem.objects.values("product__name", "product__category__name")
#             .annotate(total_sold=Sum("quantity"), total_sales=Sum("subtotal"))
#             .order_by("-total_sold")[:5]
#         )
#         top_sold_list = [
#             {
#                 "name": item["product__name"],
#                 "category": item["product__category__name"],
#                 "quantity_sold": item["total_sold"],
#                 "sales_value": float(item["total_sales"] or 0),
#             }
#             for item in top_products
#         ]

#         # ✅ Final Response
#         data = {
#             "summary": {
#                 "organization": user.organization.name if user.organization else "",
#                 "total_products": total_products,
#                 "total_suppliers": total_suppliers,
#                 "low_stock_items": low_stock_items,
#                 "total_stock_value_cost": float(total_stock_value_cost),
#                 "total_stock_value_retail": float(total_stock_value_retail),
#             },
#             "charts": {
#                 "stock_value_by_month": stock_value_chart,
#                 "sales_trend_last_7_days": sales_chart,
#                 "category_distribution": category_chart,
#             },
#             "top_products_sold": top_sold_list,
#         }
#         return Response(data)



# views.py




