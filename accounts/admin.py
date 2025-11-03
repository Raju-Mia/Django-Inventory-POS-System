from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import Organization, CustomUser, OtpTypes, VerificationOTP, VerificationTokens


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
    list_display = ['name', 'email', 'phone', 'is_active', 'total_users', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def total_users(self, obj):
        count = obj.customusers.count()
        # Adjust app name if CustomUser belongs to 'accounts' app
        url = reverse('admin:accounts_customuser_changelist') + f'?organization__id__exact={obj.id}'
        return format_html('<a href="{}">{} users</a>', url, count)
    total_users.short_description = 'Users'
    


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




# =====================================================
# VerificationTokens Admin
# =====================================================
@admin.register(VerificationTokens)
class VerificationTokensAdmin(admin.ModelAdmin):
    list_display = ['user', 'token_type', 'token_validity', 'created_at', 'token_life_time']
    list_filter = ['token_type', 'created_at']
    search_fields = ['user__email', 'user__phone', 'token']
    readonly_fields = ['id', 'created_at', 'token_validity_status']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Token Information', {
            'fields': ('id', 'user', 'token_type', 'token', 'token_life_time')
        }),
        ('Validity', {
            'fields': ('token_validity_status',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def token_validity(self, obj):
        is_valid, message = obj.token_is_valid()
        if is_valid:
            return format_html('<span style="background:#28a745; color:white; padding:3px 8px; border-radius:3px;">✓ Valid</span>')
        else:
            return format_html('<span style="background:#dc3545; color:white; padding:3px 8px; border-radius:3px;">✗ Expired</span>')
    token_validity.short_description = 'Validity'
    
    def token_validity_status(self, obj):
        is_valid, message = obj.token_is_valid()
        color = '#28a745' if is_valid else '#dc3545'
        icon = '✓' if is_valid else '✗'
        
        status = f"""
        <div style="padding:15px; background:#f8f9fa; border-left:4px solid {color}; border-radius:4px;">
            <h3 style="margin:0 0 10px 0; color:{color};">{icon} {message}</h3>
            <p style="margin:5px 0;"><strong>Created:</strong> {obj.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin:5px 0;"><strong>Lifetime:</strong> {obj.token_life_time} minutes</p>
            <p style="margin:5px 0;"><strong>Token Type:</strong> {obj.get_token_type_display()}</p>
        </div>
        """
        return mark_safe(status)
    token_validity_status.short_description = 'Token Validity Status'


# =====================================================
# VerificationOTP Admin
# =====================================================
@admin.register(VerificationOTP)
class VerificationOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_type', 'verification_otp', 'used_status', 'otp_validity', 'created_at']
    list_filter = ['otp_type', 'used_status', 'created_at']
    search_fields = ['user__email', 'user__phone', 'verification_otp', 'message_sid']
    readonly_fields = ['id', 'created_at', 'updated_at', 'otp_status_details']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('id', 'user', 'otp_type', 'verification_otp', 'message_sid')
        }),
        ('Status & Validity', {
            'fields': ('used_status', 'verification_otp_life_time', 'verification_otp_timestamp', 'otp_status_details')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def otp_validity(self, obj):
        if obj.used_status:
            return format_html('<span style="background:#6c757d; color:white; padding:3px 8px; border-radius:3px;">Used</span>')
        elif obj.otp_is_valid():
            return format_html('<span style="background:#28a745; color:white; padding:3px 8px; border-radius:3px;">✓ Valid</span>')
        else:
            return format_html('<span style="background:#dc3545; color:white; padding:3px 8px; border-radius:3px;">✗ Expired</span>')
    otp_validity.short_description = 'Validity'
    
    def otp_status_details(self, obj):
        is_valid = obj.otp_is_valid()
        
        if obj.used_status:
            status_color = '#6c757d'
            status_text = 'Used'
            icon = '✓'
        elif is_valid:
            status_color = '#28a745'
            status_text = 'Valid & Unused'
            icon = '✓'
        else:
            status_color = '#dc3545'
            status_text = 'Expired'
            icon = '✗'
        
        details = f"""
        <div style="padding:15px; background:#f8f9fa; border-left:4px solid {status_color}; border-radius:4px;">
            <h3 style="margin:0 0 10px 0; color:{status_color};">{icon} {status_text}</h3>
            <table style="width:100%; border-collapse: collapse;">
                <tr><td style="padding:5px; font-weight:bold;">OTP Code:</td><td style="padding:5px;">{obj.verification_otp or 'N/A'}</td></tr>
                <tr><td style="padding:5px; font-weight:bold; background:#f9f9f9;">OTP Type:</td><td style="padding:5px; background:#f9f9f9;">{obj.get_otp_type_display()}</td></tr>
                <tr><td style="padding:5px; font-weight:bold;">Lifetime:</td><td style="padding:5px;">{obj.verification_otp_life_time} minutes</td></tr>
                <tr><td style="padding:5px; font-weight:bold; background:#f9f9f9;">Used Status:</td><td style="padding:5px; background:#f9f9f9;">{'Yes' if obj.used_status else 'No'}</td></tr>
                <tr><td style="padding:5px; font-weight:bold;">Created At:</td><td style="padding:5px;">{obj.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            </table>
        </div>
        """
        return mark_safe(details)
    otp_status_details.short_description = 'OTP Status Details'
    
    actions = ['mark_as_used']
    
    def mark_as_used(self, request, queryset):
        updated = queryset.update(used_status=True)
        self.message_user(request, f'{updated} OTP(s) marked as used.')
    mark_as_used.short_description = 'Mark selected OTPs as used'





