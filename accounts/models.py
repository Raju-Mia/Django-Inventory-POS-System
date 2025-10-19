# accounts/models.py
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
    # logo = models.ImageField(upload_to='organization/logo/', blank=True)
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

