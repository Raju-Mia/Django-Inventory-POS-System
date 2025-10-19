from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import Organization, CustomUser


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Q
from django.utils import timezone



# =====================================================
# Organization Admin
# =====================================================
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_active', 'total_users', 'total_products', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at', 'organization_stats']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'email', 'phone', 'address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Statistics', {
            'fields': ('organization_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_users(self, obj):
        count = obj.customusers.count()
        url = reverse('admin:core_customuser_changelist') + f'?organization__id__exact={obj.id}'
        return format_html('<a href="{}">{} users</a>', url, count)
    total_users.short_description = 'Users'
    
    def total_products(self, obj):
        count = obj.products.count()
        url = reverse('admin:core_product_changelist') + f'?organization__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    total_products.short_description = 'Products'
    
    def organization_stats(self, obj):
        stats = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr><th style="text-align:left; padding:8px; background:#f5f5f5;">Metric</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Count</th></tr>
            <tr><td style="padding:8px;">Total Users</td><td style="text-align:right; padding:8px;">{obj.customusers.count()}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Products</td><td style="text-align:right; padding:8px; background:#f9f9f9;">{obj.products.count()}</td></tr>
            <tr><td style="padding:8px;">Total Customers</td><td style="text-align:right; padding:8px;">{obj.customers.count()}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Suppliers</td><td style="text-align:right; padding:8px; background:#f9f9f9;">{obj.suppliers.count()}</td></tr>
            <tr><td style="padding:8px;">Total Sales</td><td style="text-align:right; padding:8px;">{obj.sales.count()}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Total Purchases</td><td style="text-align:right; padding:8px; background:#f9f9f9;">{obj.purchases.count()}</td></tr>
        </table>
        """
        return mark_safe(stats)
    organization_stats.short_description = 'Organization Statistics'


# =====================================================
# CustomUser Admin
# =====================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'get_full_name', 'role', 'organization', 'is_owner', 'is_verified', 'is_active', 'status_badge', 'created_at']
    list_filter = ['role', 'is_active', 'is_verified', 'is_owner', 'is_terminated', 'is_block', 'organization', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    readonly_fields = ['id', 'last_login', 'created_at', 'updated_at', 'user_activity']
    
    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'profile_picture')
        }),
        ('Organization & Role', {
            'fields': ('organization', 'role', 'is_owner')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Status Flags', {
            'fields': ('is_verified', 'is_terminated', 'is_block')
        }),
        ('Activity', {
            'fields': ('user_activity',),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 
                      'phone', 'organization', 'role', 'is_staff', 'is_active')
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else "-"
    get_full_name.short_description = 'Full Name'
    
    def status_badge(self, obj):
        if obj.is_terminated:
            return format_html('<span style="background:#dc3545; color:white; padding:3px 8px; border-radius:3px;">Terminated</span>')
        elif obj.is_block:
            return format_html('<span style="background:#ffc107; color:black; padding:3px 8px; border-radius:3px;">Blocked</span>')
        elif not obj.is_verified:
            return format_html('<span style="background:#17a2b8; color:white; padding:3px 8px; border-radius:3px;">Unverified</span>')
        elif obj.is_active:
            return format_html('<span style="background:#28a745; color:white; padding:3px 8px; border-radius:3px;">Active</span>')
        else:
            return format_html('<span style="background:#6c757d; color:white; padding:3px 8px; border-radius:3px;">Inactive</span>')
    status_badge.short_description = 'Status'
    
    def user_activity(self, obj):
        sales_count = obj.created_sales.count()
        purchases_count = obj.created_purchases.count()
        stock_movements = obj.stock_movements_created.count()
        
        activity = f"""
        <table style="width:100%; border-collapse: collapse;">
            <tr><th style="text-align:left; padding:8px; background:#f5f5f5;">Activity</th>
                <th style="text-align:right; padding:8px; background:#f5f5f5;">Count</th></tr>
            <tr><td style="padding:8px;">Sales Created</td><td style="text-align:right; padding:8px;">{sales_count}</td></tr>
            <tr><td style="padding:8px; background:#f9f9f9;">Purchases Created</td><td style="text-align:right; padding:8px; background:#f9f9f9;">{purchases_count}</td></tr>
            <tr><td style="padding:8px;">Stock Movements</td><td style="text-align:right; padding:8px;">{stock_movements}</td></tr>
        </table>
        """
        return mark_safe(activity)
    user_activity.short_description = 'User Activity'


