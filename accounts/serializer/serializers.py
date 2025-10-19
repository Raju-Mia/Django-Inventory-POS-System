from rest_framework import serializers
from core.models import Organization, CustomUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import random
import string

from datetime import timedelta
from django.utils import timezone


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        try:
            user = CustomUser.objects.get(phone=phone_number)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({'error': 'Invalid phone number or password'})

        # Authenticate user
        if not user.check_password(password):
            raise serializers.ValidationError({'error': 'Invalid phone number or password'})

        if not user.is_verified:
            raise serializers.ValidationError({'error': 'Phone number is not verified'})

        # If authentication is successful, call the parent `validate` method
        return super().validate({
            'username': user.username,  # Set username internally for token generation
            'password': password
        })






class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(write_only=True, required=False)  # Add this field

    class Meta:
        model = CustomUser
        fields = [
            'id', 'full_name', 'phone_number', 'organization', 'organization_name', 'address', 'password'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extract organization_name from validated_data
        organization_name = validated_data.pop('organization_name', None)

        # Generate a random username
        base_username = validated_data.get('full_name', '').replace(' ', '').lower()
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{base_username}{random_suffix}"

        # Ensure username uniqueness
        while CustomUser.objects.filter(username=username).exists():
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"{base_username}{random_suffix}"

        # Create the user
        user = CustomUser(
            phone_number=validated_data['phone_number'],
            full_name=validated_data['full_name'],
            address=validated_data.get('address', ''),
            username=username
        )
        user.set_password(validated_data['password'])

        # Create the organization if organization_name is provided
        if organization_name:
            organization, created = Organization.objects.get_or_create(
                name=organization_name,
                defaults={
                    'address': validated_data.get('address', ''),
                    'created_by': user  # Assign the user as the creator of the organization
                },
                
            )
            user.organization = organization

        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(write_only=True, required=False)  # Add this field

    class Meta:
        model = CustomUser
        fields = [
            'id', 'full_name', 'phone_number', 'organization', 'organization_name', 'address', 'password'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        organization_name = validated_data.pop('organization_name', None)

        # Generate random username
        base_username = validated_data.get('full_name', '').replace(' ', '').lower()
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{base_username}{random_suffix}"
        while CustomUser.objects.filter(username=username).exists():
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"{base_username}{random_suffix}"

        # 🔑 Force role=manager here
        user = CustomUser(
            phone_number=validated_data['phone_number'],
            full_name=validated_data['full_name'],
            address=validated_data.get('address', ''),
            username=username,
            role="manager",   # 👈 FIXED
        )
        user.set_password(validated_data['password'])
        user.save()

        # ✅ Create or assign organization
        if organization_name:
            organization, created = Organization.objects.get_or_create(
                name=organization_name,
                defaults={'address': validated_data.get('address', '')}
            )
        else:
            # fallback: use full_name if no org name provided
            organization = Organization.objects.create(
                name=f"Org-{user.full_name}",
                address=validated_data.get('address', ''),
                created_by=user
            )

        user.organization = organization
        user.save(update_fields=["organization"])

        return user


# UserLoginSerializer is used to serialize the user login data
class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)




class UserUpdateProfileSerializer(serializers.ModelSerializer):
    organization_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'contact_number', 'bin', 'address', 'profile_picture', 'organization_name']
        
    def get_organization_name(self, obj):
        if obj.organization:
            return obj.organization.name
        return None




class UserProfileDetailSerializer(serializers.ModelSerializer):
    plan_name = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'contact_number', 'bin', 'address', 'profile_picture', 'plan_name', 'organization_name']

    def get_plan_name(self, obj):
        subscription = obj.subscription_set.filter(active_status=True).first()
        if subscription and subscription.subscription_plan:
            return subscription.subscription_plan.plan_category
        return None

    def get_organization_name(self, obj):
        if obj.organization:
            return obj.organization.name
        return None





# UserDeleteProfilePictureSerializer is used to serialize the user profile picture delete data
class UserDeleteProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['profile_picture']




class OTPVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()



# ResendOTPSerializer is used to serialize the resend OTP data
class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()



# UserChangePasswordSerializer is used to serialize the user change password data
class PhoneNumberOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    # Validate method to check if the user with the given phone number exists
    def validate_phone_number(self, value):
        try:
            user = CustomUser.objects.get(phone_number=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this phone number does not exist.")
        return value



# ForgetPasswordSerializer is used to serialize the forget password data
class ForgetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    # password = serializers.CharField()

    # Validate method to check if the user with the given phone number exists
    def validate(self, data):
        phone_number = data.get('phone_number')
        # password = data.get('password')
        try:
            user = CustomUser.objects.get(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this phone number does not exist.")
        return data



class VerifyForgetPasswordOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp = serializers.CharField()


    



# ChangePasswordSerializer is used to serialize the change password data
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()

    
class SetNewPasswordSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    token_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True)
    
    
    class Meta:
        fields = ["user_id", "token_id", "password"]


    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value
    