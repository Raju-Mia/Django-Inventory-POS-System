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
    organization_name = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(
        choices=CustomUser.ROLE_CHOICES, required=False
    )

    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email', 'organization',
            'organization_name', 'password', 'role'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        organization_name = validated_data.pop('organization_name', None)
        role = validated_data.pop('role', 'manager')  # default if not provided

        # Generate unique username
        base_username = validated_data.get('first_name', '').replace(' ', '').lower() or "user"
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{base_username}{random_suffix}"
        while CustomUser.objects.filter(username=username).exists():
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"{base_username}{random_suffix}"

        # Create user
        user = CustomUser(
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            username=username,
            role=role,
        )
        user.set_password(validated_data['password'])
        user.save()

        # Create or assign organization
        if organization_name:
            organization, _ = Organization.objects.get_or_create(
                name=organization_name,
            )
        else:
            organization = Organization.objects.create(
                name=f"Org-{user.first_name or 'User'}"
            )

        user.organization = organization
        user.save(update_fields=["organization"])

        return user



# UserLoginSerializer is used to serialize the user login data
class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)




class UserUpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'profile_picture']
        




class UserProfileDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'role', 'profile_picture', 'organization_name']


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
    email = serializers.CharField()
    otp = serializers.CharField()



# ResendOTPSerializer is used to serialize the resend OTP data
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.CharField()



# UserChangePasswordSerializer is used to serialize the user change password data
class PhoneNumberOTPSerializer(serializers.Serializer):
    email = serializers.CharField()

    # Validate method to check if the user with the given phone number exists
    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value



# ForgetPasswordSerializer is used to serialize the forget password data
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()

    # Validate method to check if the user with the given phone number exists
    def validate(self, data):
        email = data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this Email does not exist.")
        return data



class VerifyForgetPasswordOTPSerializer(serializers.Serializer):
    email = serializers.CharField()
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
    