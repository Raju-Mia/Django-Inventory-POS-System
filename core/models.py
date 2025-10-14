# core/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime
from django.conf import settings
from django.utils.timezone import timedelta


# -----------------------
# Organization
# -----------------------
class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name



# -----------------------
# Custom User (email-based)
# -----------------------
class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="customusers", null=True, blank=True)
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("staff", "Staff"),
        ("operator", "Operator"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="manager")
    profile_picture = models.ImageField(upload_to='customuser/profile_images/', blank=True)
    is_owner = models.BooleanField(default=False)

    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_terminated = models.BooleanField(default=False)
    is_block = models.BooleanField(default=False)

    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.email
    

    def save(self, *args, **kwargs):
        # Optional: if username empty, set it from email (or a generated value)
        if not self.username and self.email:
            self.username = self.email
        super().save(*args, **kwargs)


#============================ OTP START ========================
class TokenTypes(models.TextChoices):
    email_verification = "email verification"
    password_reset = "password reset"
    phone_number_verification = "phone number verification"


class VerificationTokens(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    token_type = models.CharField(max_length=100, choices=TokenTypes.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token_life_time = models.IntegerField(default=5)

    def __str__(self):
        if self.user.phone:
            x = self.user.phone
        else:
            x = str(self.id)
        return self.token_type + " " + str(x) + str(self.created_at)

    @property
    def is_valid(self):
        """
        checks tokens validity
        """
        otp_life_time = 5
        return self.created_at + timedelta(minutes=otp_life_time) > timezone.now()

    def code_is_valid(self):
        code_life_time = 10
        return self.created_at + timedelta(minutes=code_life_time) > timezone.now()
    
    
    def token_is_valid(self):
        if self.created_at + timedelta(minutes=self.token_life_time) > timezone.now():
            return True, "Token is valid"
        else:
            return False, "Token has expired"



class OtpTypes(models.TextChoices):
    email_verification = "Email Verification"
    password_reset = "Password Reset"
    phone_number_verification = "Phone Number Verification"



class VerificationOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    otp_type = models.CharField(max_length=100, choices=OtpTypes.choices)
    message_sid = models.CharField(max_length=256, blank=True,null=True)
    verification_otp = models.CharField(max_length=6, blank=True,null=True)
    verification_otp_life_time = models.IntegerField(default=5)
    verification_otp_timestamp = models.DateTimeField(null=True, blank=True)
    used_status = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user.phone:
            x = self.user.phone
        else:
            x = str(self.id)
        return str(x) + str(self.created_at)

    @property
    def is_valid(self):
        """
        checks tokens validity
        """
        verification_otp_life_time = 5
        return self.created_at + timedelta(minutes=verification_otp_life_time) > timezone.now()

    def otp_is_valid(self):
        verification_otp_life_time = 10
        return self.created_at + timedelta(minutes=verification_otp_life_time) > timezone.now()

#========================== OTP END ==========================




# -----------------------
# Category
# -----------------------
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.organization})"

# -----------------------
# Product
# -----------------------
class Product(models.Model):
    STATUS_CHOICES = [("in_stock", "In Stock"), ("low_stock", "Low Stock"), ("out_of_stock", "Out of Stock"), ("active", "Active"), ("inactive", "Inactive"), ("archived", "Archived")]

    UNIT_CHOICES = [("kg", "KG"), ("litre", "Litre"), ("loaf", "Loaf"), ("gram", "Gram"), ("piece", "Piece"), ("box", "Box"), ("set", "Set")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    product_id = models.CharField(max_length=100, unique=True, blank=True)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=50, choices=UNIT_CHOICES, default="piece")
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.IntegerField(default=0)
    current_stock = models.IntegerField(default=0)
    barcode = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_stock")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

# -----------------------
# Supplier
# -----------------------
class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

# -----------------------
# Customer
# -----------------------
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="customers")
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# -----------------------
# Sale & SaleItem (POS)
# -----------------------
class Sale(models.Model):
    PAYMENT_STATUS = [("paid", "Paid"), ("due", "Due"), ("partial", "Partial")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="sales")
    invoice_number = models.CharField(max_length=255, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="paid")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey("core.CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_sales")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sale {self.invoice_number}"

class SaleItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product} x {self.quantity}"

# -----------------------
# Purchase & PurchaseItem
# -----------------------
class Purchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="purchases")
    purchase_number = models.CharField(max_length=255, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="purchases")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default="received")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey("core.CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_purchases")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Purchase {self.purchase_number}"

class PurchaseItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="purchase_items")
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product} x {self.quantity}"

# -----------------------
# StockMovement
# -----------------------
class StockMovement(models.Model):
    MOVEMENT_CHOICES = [("in", "In"), ("out", "Out"), ("adjust", "Adjustment")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="stock_movements")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_movements")
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES)
    quantity = models.IntegerField()
    reference_number = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey("core.CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements_created")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product} {self.movement_type} {self.quantity}"

# -----------------------
# ContactMessage
# -----------------------
class ContactMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Contact from {self.name}: {self.subject}"
