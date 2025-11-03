# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import (
    Category, Product, Supplier, Customer,
    Sale, SaleItem, Purchase, PurchaseItem, StockMovement, ContactMessage
)

from accounts.models import Organization, CustomUser

# =====================================================
# Custom Admin Site Configuration
# =====================================================
admin.site.site_header = 'Inventory Management System'
admin.site.site_title = 'IMS Admin Portal'
admin.site.index_title = 'Welcome to Inventory Management System Administration'








# =====================================================
# Category Admin
# =====================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'product_count', 'created_at']
    list_filter = ['organization', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'name', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:core_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    product_count.short_description = 'Products'


# =====================================================
# Product Admin
# =====================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'name', 'sku', 'category', 'organization', 'current_stock', 
                   'stock_status', 'sell_price', 'status', 'created_at']
    list_filter = ['status', 'organization', 'category', 'unit', 'created_at']
    search_fields = ['name', 'sku', 'product_id', 'barcode', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'profit_margin', 'product_details']
    ordering = ['-created_at']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'product_id', 'name', 'sku', 'category', 'barcode')
        }),
        ('Pricing & Inventory', {
            'fields': ('unit', 'purchase_price', 'sell_price', 'profit_margin', 
                      'current_stock', 'reorder_level', 'status')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Product Analytics', {
            'fields': ('product_details',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        if obj.current_stock <= 0:
            return format_html('<span style="background:#dc3545; color:white; padding:3px 8px; border-radius:3px;">Out of Stock</span>')
        elif obj.current_stock <= obj.reorder_level:
            return format_html('<span style="background:#ffc107; color:black; padding:3px 8px; border-radius:3px;">Low Stock</span>')
        else:
            return format_html('<span style="background:#28a745; color:white; padding:3px 8px; border-radius:3px;">In Stock</span>')
    stock_status.short_description = 'Stock Status'
    
    def profit_margin(self, obj):
        if obj.purchase_price > 0:
            margin = ((obj.sell_price - obj.purchase_price) / obj.purchase_price) * 100
            color = '#28a745' if margin > 0 else '#dc3545'
            return format_html('<span style="color:{}; font-weight:bold;">{:.2f}%</span>', color, margin)
        return '-'
    profit_margin.short_description = 'Profit Margin'
    
    def product_details(self, obj):
        sales = obj.sale_items.aggregate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('subtotal')
        )
        purchases = obj.purchase_items.aggregate(
            total_purchased=Sum('quantity'),
            total_cost=Sum('subtotal')
        )
        
        details = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr><th colspan="2" style="text-align:left; padding:8px; background:#007bff; color:white;">Sales Information</th></tr>
            <tr><td style="padding:8px;">Total Units Sold</td><td style="text-align:right; padding:8px;">{sales['total_sold'] or 0}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Revenue</td><td style="text-align:right; padding:8px; background:#f9f9f9;">৳{sales['total_revenue'] or 0:,.2f}</td></tr>
            
            <tr><th colspan="2" style="text-align:left; padding:8px; background:#28a745; color:white;">Purchase Information</th></tr>
            <tr><td style="padding:8px;">Total Units Purchased</td><td style="text-align:right; padding:8px;">{purchases['total_purchased'] or 0}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Cost</td><td style="text-align:right; padding:8px; background:#f9f9f9;">৳{purchases['total_cost'] or 0:,.2f}</td></tr>
            
            <tr><th colspan="2" style="text-align:left; padding:8px; background:#6c757d; color:white;">Current Stock</th></tr>
            <tr><td style="padding:8px;">Available Stock</td><td style="text-align:right; padding:8px;">{obj.current_stock} {obj.unit}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Reorder Level</td><td style="text-align:right; padding:8px; background:#f9f9f9;">{obj.reorder_level} {obj.unit}</td></tr>
        </table>
        """
        return mark_safe(details)
    product_details.short_description = 'Product Analytics'


# =====================================================
# Supplier Admin
# =====================================================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'organization', 
                   'is_active', 'total_purchases', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at', 'supplier_stats']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'name', 'contact_person')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Supplier Statistics', {
            'fields': ('supplier_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_purchases(self, obj):
        count = obj.purchases.count()
        url = reverse('admin:core_purchase_changelist') + f'?supplier__id__exact={obj.id}'
        return format_html('<a href="{}">{} purchases</a>', url, count)
    total_purchases.short_description = 'Purchases'
    
    def supplier_stats(self, obj):
        purchases = obj.purchases.aggregate(
            total_purchases=Count('id'),
            total_amount=Sum('total_amount')
        )
        
        stats = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr><th style="text-align:left; padding:8px; background:#f5f5f5;">Metric</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Value</th></tr>
            <tr><td style="padding:8px;">Total Purchases</td><td style="text-align:right; padding:8px;">{purchases['total_purchases'] or 0}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Amount Paid</td><td style="text-align:right; padding:8px; background:#f9f9f9;">৳{purchases['total_amount'] or 0:,.2f}</td></tr>
        </table>
        """
        return mark_safe(stats)
    supplier_stats.short_description = 'Supplier Statistics'


# =====================================================
# Customer Admin
# =====================================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'mobile', 'organization', 'payment_total', 
                   'due_amount', 'is_active', 'total_sales', 'created_at']
    list_filter = ['is_active', 'organization', 'created_at']
    search_fields = ['name', 'email', 'mobile']
    readonly_fields = ['id', 'created_at', 'updated_at', 'customer_stats']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'name', 'email', 'mobile', 'address')
        }),
        ('Financial Information', {
            'fields': ('payment_total', 'due_amount')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Customer Statistics', {
            'fields': ('customer_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_sales(self, obj):
        count = obj.sales.count()
        url = reverse('admin:core_sale_changelist') + f'?customer__id__exact={obj.id}'
        return format_html('<a href="{}">{} sales</a>', url, count)
    total_sales.short_description = 'Sales'
    
    def customer_stats(self, obj):
        sales = obj.sales.aggregate(
            total_sales=Count('id'),
            total_amount=Sum('net_total'),
            total_paid=Sum('paid_amount')
        )
        
        stats = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr><th style="text-align:left; padding:8px; background:#f5f5f5;">Metric</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Value</th></tr>
            <tr><td style="padding:8px;">Total Transactions</td><td style="text-align:right; padding:8px;">{sales['total_sales'] or 0}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Purchase Amount</td><td style="text-align:right; padding:8px; background:#f9f9f9;">৳{sales['total_amount'] or 0:,.2f}</td></tr>
            <tr><td style="padding:8px;">Total Paid</td><td style="text-align:right; padding:8px;">৳{sales['total_paid'] or 0:,.2f}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Outstanding Due</td><td style="text-align:right; padding:8px; background:#f9f9f9;">৳{obj.due_amount:,.2f}</td></tr>
        </table>
        """
        return mark_safe(stats)
    customer_stats.short_description = 'Customer Statistics'


# =====================================================
# SaleItem Inline
# =====================================================
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['id', 'subtotal']
    fields = ['product', 'quantity', 'unit_price', 'subtotal']
    can_delete = False


# =====================================================
# Sale Admin
# =====================================================
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'organization', 'total_amount', 
                   'discount', 'net_total', 'paid_amount', 'payment_badge', 
                   'created_by', 'created_at']
    list_filter = ['payment_status', 'organization', 'created_at', 'created_by']
    search_fields = ['invoice_number', 'customer__name', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sale_summary']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [SaleItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'invoice_number', 'customer', 'created_by')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'discount', 'vat', 'net_total', 'paid_amount', 'payment_status')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Sale Summary', {
            'fields': ('sale_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def payment_badge(self, obj):
        colors = {
            'paid': '#28a745',
            'due': '#dc3545',
            'partial': '#ffc107'
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_badge.short_description = 'Payment Status'
    
    def sale_summary(self, obj):
        items = obj.items.all()
        due = obj.net_total - obj.paid_amount
        
        items_html = ""
        for item in items:
            items_html += f"<tr><td style='padding:8px;'>{item.product.name}</td><td style='text-align:right; padding:8px;'>{item.quantity}</td><td style='text-align:right; padding:8px;'>৳{item.unit_price:,.2f}</td><td style='text-align:right; padding:8px; background:#f9f9f9;'>৳{item.subtotal:,.2f}</td></tr>"
        
        summary = f"""
        <table style="width:100%; border-collapse: collapse; margin-bottom:20px;">
            <tr><th colspan="4" style="text-align:left; padding:8px; background:#007bff; color:white;">Sale Items</th></tr>
            <tr><th style="text-align:left; padding:8px; background:#f5f5f5;">Product</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Qty</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Unit Price</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Subtotal</th></tr>
            {items_html}
        </table>
        
        <table style="width:100%; border-collapse: collapse;">
            <tr><th colspan="2" style="text-align:left; padding:8px; background:#28a745; color:white;">Payment Summary</th></tr>
            <tr><td style="padding:8px;">Total Amount</td><td style="text-align:right; padding:8px;">৳{obj.total_amount:,.2f}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Discount</td><td style="text-align:right; padding:8px; background:#f9f9f9;">৳{obj.discount:,.2f}</td></tr>
            <tr><td style="padding:8px;">VAT</td><td style="text-align:right; padding:8px;">৳{obj.vat:,.2f}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9; font-weight:bold;">Net Total</td><td style="text-align:right; padding:8px; background:#f9f9f9; font-weight:bold;">৳{obj.net_total:,.2f}</td></tr>
            <tr><td style="padding:8px;">Paid Amount</td><td style="text-align:right; padding:8px;">৳{obj.paid_amount:,.2f}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9; font-weight:bold; color:#dc3545;">Due Amount</td><td style="text-align:right; padding:8px; background:#f9f9f9; font-weight:bold; color:#dc3545;">৳{due:,.2f}</td></tr>
        </table>
        """
        return mark_safe(summary)
    sale_summary.short_description = 'Sale Summary'


# =====================================================
# PurchaseItem Inline
# =====================================================
class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ['id', 'subtotal']
    fields = ['product', 'quantity', 'unit_price', 'subtotal']
    can_delete = False


# =====================================================
# Purchase Admin
# =====================================================
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_number', 'supplier', 'organization', 'total_amount', 
                   'status', 'created_by', 'created_at']
    list_filter = ['status', 'organization', 'created_at', 'created_by']
    search_fields = ['purchase_number', 'supplier__name', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at', 'purchase_summary']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [PurchaseItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'purchase_number', 'supplier', 'created_by')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Purchase Summary', {
            'fields': ('purchase_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def purchase_summary(self, obj):
        items = obj.items.all()
        
        items_html = ""
        for item in items:
            items_html += f"<tr><td style='padding:8px;'>{item.product.name}</td><td style='text-align:right; padding:8px;'>{item.quantity}</td><td style='text-align:right; padding:8px;'>৳{item.unit_price:,.2f}</td><td style='text-align:right; padding:8px; background:#f9f9f9;'>৳{item.subtotal:,.2f}</td></tr>"
        
        summary = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr><th colspan="4" style="text-align:left; padding:8px; background:#28a745; color:white;">Purchase Items</th></tr>
            <tr><th style="text-align:left; padding:8px; background:#f5f5f5;">Product</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Qty</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Unit Price</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Subtotal</th></tr>
            {items_html}
            <tr><td colspan="3" style="padding:8px; font-weight:bold; text-align:right;">Total Amount:</td>
                <td style="text-align:right; padding:8px; font-weight:bold; background:#f9f9f9;">৳{obj.total_amount:,.2f}</td></tr>
        </table>
        """
        return mark_safe(summary)
    purchase_summary.short_description = 'Purchase Summary'


# =====================================================
# StockMovement Admin
# =====================================================
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'organization', 
                   'reference_number', 'created_by', 'created_at']
    list_filter = ['movement_type', 'organization', 'created_at', 'created_by']
    search_fields = ['product__name', 'reference_number', 'notes']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'product', 'movement_type', 'quantity')
        }),
        ('Reference', {
            'fields': ('reference_number', 'notes', 'created_by')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# =====================================================
# ContactMessage Admin
# =====================================================
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'read_badge', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['id', 'created_at', 'formatted_message']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('id', 'name', 'email', 'subject')
        }),
        ('Message', {
            'fields': ('formatted_message',)
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def read_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="background:#28a745; color:white; padding:3px 8px; border-radius:3px;">✓ Read</span>')
        else:
            return format_html('<span style="background:#dc3545; color:white; padding:3px 8px; border-radius:3px;">✗ Unread</span>')
    read_badge.short_description = 'Status'
    
    def formatted_message(self, obj):
        return format_html('<div style="padding:15px; background:#f8f9fa; border-left:4px solid #007bff; border-radius:4px;">{}</div>', obj.message)
    formatted_message.short_description = 'Message Content'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} message(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected messages as unread'


