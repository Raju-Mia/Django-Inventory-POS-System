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
    # send_otp_to_email,
)


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
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        if not phone_number or not password:
            return Response(
                {'error': 'Phone number and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = CustomUser.objects.filter(phone=phone_number).first()
        if user is None:
            return Response(
                {'error': 'Invalid phone number or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Invalid phone number or password.'},  # do not expose "wrong password" separately
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_verified:
            return Response(
                {'error': 'Account is not verified. Please verify your phone number.', 'code': 'not_verified'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated. Please contact your administration!.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if user.is_terminated:
            return Response(
                {'error': 'Account is Terminated. Please contact your administration!.'},
                status=status.HTTP_403_FORBIDDEN
            )
   
        # 🔑 Generate tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        
        #check the user role
        if user.role == "manager":
            new_user = user
        elif user.role == "operator":
            new_user = user.organization.created_by
            
        print("The user is: ", user)



        user_info = {
            'phone_number': user.phone,
            'full_name': user.full_name,
            'organization_name': user.organization.name if user.organization else "Unknown Organization",
            'role': user.role,
            'address': user.address,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
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




#==================== signup(Phone) a user  ===============
class UserSignUpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            full_name = serializer.validated_data['full_name']
            password = serializer.validated_data['password']
            organization_name = serializer.validated_data.get('organization_name')

            # ✅ Always set role as manager
            role = "manager"

            # Check if phone already exists
            try:
                user = CustomUser.objects.get(phone=phone_number)

                if user.is_verified:
                    return Response(
                        {'error': 'Phone number already registered.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Update existing unverified user
                    user.full_name = full_name
                    user.address = serializer.validated_data.get('address', '')
                    user.role = role
                    user.set_password(password)
                    user.save()
                    
                    
                    # Ensure organization exists/updates
                    if user.organization:
                        user_org = user.organization
                        user_org.name = organization_name or f"Org-{full_name}"
                        user_org.created_by = user
                        user_org.save()
                    else:
                        org = Organization.objects.create(
                            name=organization_name or f"Org-{full_name}",
                            created_by=user
                        )
                        user.organization = org
                        user.save(update_fields=["organization"])
                        
                        
                    #------------ OTP Manage --------
                    # Filter all VerificationOTP objects for the given user
                    user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
                    user_verification_otp_objects.delete()
                    if user:
                        send_phone_verification_otp(user)
                    else:
                        return Response({"message": "User Verify OTP not send!"},status=status.HTTP_400_BAD_REQUEST)
                                                
                    
                    #--------------------------------------------------------------------------------
                    # Step permissions: 🎯 GRANT ALL PERMISSIONS TO ADMIN (create or update)



                 

                    print("Permissions created or updated successfully")
                    #--------------------------------------------------------------------------------

                

                    return Response({
                        'user_id': user.id,
                        'phone_number': user.phone,
                        'message': 'User updated. Please verify your phone number.'
                    }, status=status.HTTP_200_OK)

            except CustomUser.DoesNotExist:
                # New user signup
                base_username = full_name.replace(' ', '').lower()
                random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
                username = f"{base_username}{random_suffix}"

                # Ensure username uniqueness
                while CustomUser.objects.filter(username=username).exists():
                    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
                    username = f"{base_username}{random_suffix}"

                # Save user
                user = serializer.save(username=username, role=role)
                user.otp = "123456"  # TODO: Replace with random OTP generator
                user.save()
                
                # Ensure organization exists
                if user.organization:
                    user_org = user.organization
                    user_org.name = organization_name or f"Org-{full_name}"
                    user_org.created_by = user
                    user_org.save()
                else:
                    org = Organization.objects.create(
                        name=organization_name or f"Org-{full_name}",
                        created_by=user
                    )
                    user.organization = org
                    user.save(update_fields=["organization"])
                    
                    
                #------------ OTP Manage --------
                # Filter all VerificationOTP objects for the given user
                user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
                user_verification_otp_objects.delete()
                if user:
                    send_phone_verification_otp(user)
                else:
                    return Response({"message": "User Verify OTP not send!"},status=status.HTTP_400_BAD_REQUEST)
                
                #--------------------------------------------------------------------------------
                # Step permissions: 🎯 GRANT ALL PERMISSIONS TO ADMIN
         
              
            

                return Response({
                    'user_id': user.id,
                    'phone_number': user.phone,
                    'full_name': user.full_name,
                    'message': 'User successfully registered. Please verify your phone number.'
                }, status=status.HTTP_201_CREATED)

        # Validation failed
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    
# OTPVerificationView is used to verify the OTP of a user 
class OTPVerificationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPVerificationSerializer

    # Post method to verify the OTP of a user
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            verification_otp = serializer.validated_data['otp']
            user = CustomUser.objects.get(phone=phone_number)
            
            #------------- SMS OTP Verification
            otp_verified_status,otp_obj_id,otp_verified_message = sms_otp_is_verified(user,verification_otp)
            if otp_verified_status and otp_obj_id is not None:
                # Filter all VerificationOTP objects for the given user
                user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
                user_verification_otp_objects.delete()

                # user.is_active = True
                # user.email_is_verified = True
                user.is_verified = True
                user.save()
                return Response({"message": "User verified successfully"}, status=status.HTTP_200_OK)
            
            return Response({"message": otp_verified_message}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





# ResendOTPView is used to resend the OTP to a user
class ResendOTPView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOTPSerializer

    #  Post method to resend the OTP to a user
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            try:
                user = CustomUser.objects.get(phone=phone_number)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this phone number does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            
            
            
            #------------ OTP Verification Manage --------
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()
            
            if user:
                send_phone_verification_otp(user)
            else:
                return Response({"message": "User Verify OTP not send!"},status=status.HTTP_400_BAD_REQUEST)


            response_data = {
                "message": "Reset OTP successfuly send to your phone number",
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
        serializer = ForgetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            # password = serializer.validated_data['password']
            try:
                user = CustomUser.objects.get(phone=phone_number)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this phone number does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            # user.set_password(password)

            
            #------------ OTP Verification Manage --------
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()
            
            if user:
                send_phone_verification_otp(user)
            else:
                return Response({"message": "User Verify OTP not send!"},status=status.HTTP_400_BAD_REQUEST)


            return Response({"message": "successfully otp please verify your phone number"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class VerifyForgotPasswordOTP(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyForgetPasswordOTPSerializer

    # Post method to update the password of a user
    def post(self, request):
        serializer = VerifyForgetPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            verification_otp = serializer.validated_data['otp']
            try:
                user = CustomUser.objects.get(phone=phone_number)
            except CustomUser.DoesNotExist:
                return Response({'error': 'User with this phone number does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            

            
            #------------- SMS OTP Verification
            otp_verified_status,otp_obj_id,otp_verified_message = sms_otp_is_verified(user,verification_otp)
            
            if otp_verified_status and otp_obj_id is not None:
                # Filter all VerificationOTP objects for the given user
                user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
                user_verification_otp_objects.delete()

                # user.is_active = True
                # user.email_is_verified = True
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
                {"message": "User with this phone number does not exist."},
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
            # Delete Verification Access Token
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



class UserDeleteProfilePictureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        if not user.profile_picture:  # Checks for None or empty string
            return Response({'message': 'You have no profile picture.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove profile picture
        user.profile_picture = None
        user.save()
        return Response({"message": "Profile picture deleted successfully"}, status=status.HTTP_200_OK)







