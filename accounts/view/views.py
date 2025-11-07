import random
from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import logout

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.exceptions import AuthenticationFailed, ValidationError, ParseError
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
import random, string

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
import logging
logger = logging.getLogger(__name__)


from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction

# Import Here
from accounts.serializer.serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileDetailSerializer, 
    UserSerializer, 
    OTPVerificationSerializer, 
    ResendOTPSerializer, 
    ForgetPasswordSerializer, 
    PhoneNumberOTPSerializer, 
    ChangePasswordSerializer, 
    SetNewPasswordSerializer,
    UserUpdateProfileSerializer, 
    UserDeleteProfilePictureSerializer, 
    VerifyForgetPasswordOTPSerializer
    )


from accounts.helper import (
    send_phone_verification_otp,
    sms_otp_is_verified,
    mail_otp_is_verified,
    # send_otp_to_email,
)

from accounts.utils.mail import send_mail, send_otp_mail, resend_otp_mail, send_reset_otp_mail

from accounts.models import Organization, CustomUser, TokenTypes, VerificationTokens, OtpTypes, VerificationOTP
from accounts.utils.otp import generate_otp, otp_send



#==================== Access and Refresh Token ===============
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer




class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                raise ParseError(detail="Refresh token is required.")

            # Validate the provided refresh token
            token = RefreshToken(refresh_token)

            # Get the user associated with the token
            user_id = token['user_id']  # Extract user ID from the token
            User = get_user_model()
            user = User.objects.get(id=user_id)  # Retrieve user using user_id

            # Generate a new access token
            access_token = token.access_token

            # Generate a new refresh token for the user
            new_refresh_token = RefreshToken.for_user(user)

            return Response({
                "access": str(access_token),
                "refresh": str(new_refresh_token),  # Return the new refresh token
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)




#==================== login(Phone) a user  ===============

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_verified:
            return Response(
                {'error': 'Account is not verified. Please verify your account.', 'code': 'not_verified'},
                status=status.HTTP_403_FORBIDDEN
            )
        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated. Please contact your administration!'},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.is_terminated:
            return Response(
                {'error': 'Account is terminated. Please contact your administration!'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 🔑 Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        user_info = {
            'phone_number': user.phone,
            'full_name': f"{user.first_name} {user.last_name}",
            'organization_name': user.organization.name if user.organization else "Unknown Organization",
            'role': user.role,
            # ✅ Build absolute URL for image
            'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
        }

        return Response({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': str(refresh),
            'user_info': user_info,
        }, status=status.HTTP_200_OK)




#==================== logout a user  ===============
class UserLogoutView(APIView):
    """
    Logs out the current user by blacklisting their refresh token.
    The access token will expire naturally.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # 🚫 makes refresh token unusable
        except Exception:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Successfully logged out. Token blacklisted."},
            status=status.HTTP_205_RESET_CONTENT
        )




#==================== signup(Email) a user  ===============
class UserSignUpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            first_name = serializer.validated_data.get('first_name', '')
            last_name = serializer.validated_data.get('last_name', '')
            password = serializer.validated_data['password']
            organization_name = serializer.validated_data.get('organization_name')
            role = serializer.validated_data.get('role', 'manager')  # ✅ take from frontend


            # Check if user already exists
            try:
                user = CustomUser.objects.get(email=email)

                if user.is_verified:
                    return Response(
                        {'error': 'Already registered.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Update existing unverified user
                    user.first_name = first_name
                    user.last_name = last_name
                    user.role = role
                    user.set_password(password)
                    user.save()

                    # Ensure organization
                    if user.organization:
                        org = user.organization
                        org.name = organization_name or f"Org-{first_name}"
                        org.save()
                    else:
                        org = Organization.objects.create(
                            name=organization_name or f"Org-{first_name}"
                        )
                        user.organization = org
                        user.save(update_fields=["organization"])

                    # Remove old OTPs and send new one
                    VerificationOTP.objects.filter(user=user).delete()
                    if user:
                        # Send OTP email
                        send_otp_mail(user)
                    else:
                        return Response({"message": "Email Verify mail not send!"},status=status.HTTP_400_BAD_REQUEST)

                    return Response({
                        'user_id': user.id,
                        'email': user.email,
                        'message': 'User updated. Please verify your email verification.'
                    }, status=status.HTTP_200_OK)

            except CustomUser.DoesNotExist:
                # New user registration
                base_username = first_name.replace(' ', '').lower() or "user"
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                username = f"{base_username}{random_suffix}"
                while CustomUser.objects.filter(username=username).exists():
                    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                    username = f"{base_username}{random_suffix}"

                user = CustomUser.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    role=role,
                )
                user.set_password(password)
                user.save()

                # Create organization
                org = Organization.objects.create(
                    name=organization_name or f"Org-{first_name}"
                )
                user.organization = org
                user.save(update_fields=["organization"])

                # Remove old OTPs and send new one
                VerificationOTP.objects.filter(user=user).delete()
                
                if user:
                    # Send OTP email
                    send_otp_mail(user)
                else:
                    return Response({"message": "Email Verify mail not send!"},status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    'user_id': user.id,
                    'email': user.email,
                    'message': 'User successfully registered. Please verify your email verification.'
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





    
# OTPVerificationView is used to verify the OTP of a user 
class OTPVerificationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPVerificationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        verification_otp = serializer.validated_data['otp']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if user.is_verified:
            return Response({'error': 'User is already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        
        otp_verified_status,otp_obj_id,otp_verified_message = mail_otp_is_verified(user,verification_otp)
        
        if otp_verified_status and otp_obj_id is not None:
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
            user_verification_otp_objects.delete()

            # user.is_active = True
            # user.email_is_verified = True
            user.is_verified = True
            user.save()
            return Response({"message": "User verified successfully"}, status=status.HTTP_200_OK)
        
        else:
            return Response({'error': otp_verified_message}, status=status.HTTP_400_BAD_REQUEST)
            






# ResendOTPView is used to resend the OTP to a user
class ResendOTPView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOTPSerializer

    #  Post method to resend the OTP to a user
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            

            #------------ OTP Verification Manage --------
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()
            
            if user:
                resend_otp_mail(user)
            else:
                return Response({"message": "User Verify OTP not send!"},status=status.HTTP_400_BAD_REQUEST)


            response_data = {
                "message": "Resend OTP successfuly send to your mail.",
                "user_id": user.id
            }
            return Response(
                response_data,
                status=status.HTTP_200_OK,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# UserForgetPasswordView is used to update the password of a user
class UserForgetPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgetPasswordSerializer

    # Post method to update the password of a user
    def post(self, request):
        print(request.data)
        serializer = ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            
            #------------ OTP Verification Manage --------
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()
            
            if user:
                send_reset_otp_mail(user)
            else:
                return Response({"message": "User Verify OTP not send!"},status=status.HTTP_400_BAD_REQUEST)


            return Response({"message": "successfully otp please verify your email"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class VerifyForgotPasswordOTP(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyForgetPasswordOTPSerializer

    # Post method to update the password of a user
    def post(self, request):
        serializer = VerifyForgetPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            verification_otp = serializer.validated_data['otp']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            

            
            #------------- SMS OTP Verification
            otp_verified_status,otp_obj_id,otp_verified_message = mail_otp_is_verified(user,verification_otp)
            
            if otp_verified_status and otp_obj_id is not None:
                # Filter all VerificationOTP objects for the given user
                user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
                user_verification_otp_objects.delete()

                user.is_verified = True
                user.save()
                

                # ------- one Time VerificationTokens Gerate.
                token = VerificationTokens.objects.create(
                    user=user,
                    token_type=TokenTypes.password_reset,
                    token=generate_otp(),
                    token_life_time=int(180)
                    )

                # return Response(data=get_user_details(user),status=status.HTTP_200_OK)
                response_data = {
                    "user_id": user.id,
                    "token_id":token.id,
                    "message":"Password Reset Verification Successfully Verified."
                    }
                return Response(response_data,status=status.HTTP_200_OK)
                    
            return Response(
                {'error': otp_verified_message or 'Invalid OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )
                
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# ===========API FOR CHANGING PASSWORD ============
class ChangeForgetPassword(APIView):

    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = CustomUser.objects.get(id=serializer.validated_data["user_id"])
        except CustomUser.DoesNotExist:
            return Response(
                {"message": "User does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        try:
            verification_access_token = VerificationTokens.objects.get(id=serializer.validated_data["token_id"],user=user)
        except VerificationTokens.DoesNotExist:
            return Response({"message": "Verification Token does not Exit!"},status=status.HTTP_400_BAD_REQUEST,)
        
        # Token Verification status check.
        token_verified, token_message = verification_access_token.token_is_valid()
        
        if token_verified:
            user.set_password(serializer.validated_data["password"])
            # user.password_has_changed = True
            user.save()
            verification_access_token.delete()


                           
            return Response(
                {"message":"Password has been successfully changed."},
                status=status.HTTP_200_OK
                )
        return Response({"message": "Forget Password Permission Expired"},status=status.HTTP_400_BAD_REQUEST,)





# UserChangePasswordView is used to change the password of a user
class UserChangePasswordView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    # Post method to change the password of a user
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            if not user.check_password(old_password):
                return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







class UserUpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserUpdateProfileSerializer(data=request.data, partial=True)  # Allow partial updates

        if serializer.is_valid():
            updated_fields = []

            # Loop through validated data and update fields only if provided in the request
            for field, value in serializer.validated_data.items():
                if value is not None and getattr(user, field) != value:  # Update only if value is provided and changed
                    setattr(user, field, value)
                    updated_fields.append(field)

            if updated_fields:
                user.save(update_fields=updated_fields)  # Save only the fields that were updated
                return Response({
                    "message": "Profile updated successfully",
                    "updated_fields": updated_fields,  # Return updated fields
                    "user_data": UserUpdateProfileSerializer(user).data  # Return updated user data
                }, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No changes detected."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user
        serializer = UserProfileDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)









