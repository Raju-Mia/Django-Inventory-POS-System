from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from core.models import TokenTypes, VerificationTokens, OtpTypes, VerificationOTP
from utils.otp import generate_otp, otp_send
User = get_user_model()


# Check Username Availability ==========
class CheckUsernameAvailability(APIView):
    def get(self, request):
        username = request.query_params.get('username', None)
        
        if not username:
            return Response({"error": "Username parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({"available": False, "message": "Username is already used."}, status=status.HTTP_200_OK)
        
        return Response({"available": True, "message": "Username is available."}, status=status.HTTP_200_OK)


# User is Exit Or Not=============
def user_exists(phone_or_email)-> bool:
    print("phone_or_email is: ", type(phone_or_email))
    try:
        if "@" in phone_or_email:
            # Check by email
            user_is = User.objects.filter(email=phone_or_email).exists()
            if user_is and user_is.user_is_verified:
                return True
            else:
                return False
        else:
            # Check by phone number
            user_is = User.objects.filter(phone=phone_or_email).exists()
            if user_is:
                user = User.objects.filter(phone=phone_or_email,user_is_verified=True).first()
                if user is not None and user.user_is_verified:
                    return True
                else:
                    user_list = User.objects.filter(phone=phone_or_email,user_is_verified=False).all()
                    for i in user_list:
                        print(i.id, i.phone, i.user_is_verified, type(i.phone))
                        i.delete()
                    return False
            else:
                return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False
    
    

def send_phone_verification_otp(user: User | None = None, phone_number: str | None = None) -> None:
    # return 
    if user:
        phone_number = user.phone
        if phone_number is None:
            return

    try:
        verification_otp_is,message_sid_is = otp_send(user)
        if verification_otp_is is not None and message_sid_is is not None:
            otp_type_is = "phone_number_verification"
            user_verification_otp_object = VerificationOTP.objects.create(
                user=user,
                otp_type=OtpTypes.phone_number_verification,
                message_sid=message_sid_is,
                verification_otp=verification_otp_is,
                verification_otp_timestamp=timezone.now()
                )
            print("user_verification_otp_object saved successfully.")

    except Exception as e:
        print(e)






# TODO remove returning True for every call(its for testing only)
def sms_otp_is_verified(user: User, verification_otp: str, phone_number: str | None = None) -> (bool, str):
    if user:
        print(type(verification_otp), verification_otp)
        if verification_otp == '123456':
            print("i am here---for default otp number")
            # Get the most recent VerificationOTP object for the user and OTP
            user_verification_otp_object_is = VerificationOTP.objects.filter(
                user=user
            ).order_by('-created_at').first()
            if user_verification_otp_object_is is None:
                sms_otp_error_message = "OTP has already been used."
                print("====== OTP has already been used. =====")
                return False, None, sms_otp_error_message
            
            sms_otp_obj_id = user_verification_otp_object_is.id
            sms_otp_verified_message = "Phone Verification successfully Completed!"
            return True, sms_otp_obj_id, sms_otp_verified_message
                
                
            
        else:
            # Get the most recent VerificationOTP object for the user and OTP
            user_verification_otp_object_is = VerificationOTP.objects.filter(
                user=user, verification_otp=verification_otp
            ).order_by('-created_at').first()
            
            if user_verification_otp_object_is is not None:
                if not user_verification_otp_object_is.used_status:
                    # Check if the OTP is still valid
                    otp_expiry_time = user_verification_otp_object_is.verification_otp_timestamp + timedelta(
                        minutes=user_verification_otp_object_is.verification_otp_life_time
                    )
                    print("OTP expiry time and current time:", otp_expiry_time, timezone.now())
                    if otp_expiry_time >= timezone.now():
                        # Mark the OTP as used
                        user_verification_otp_object_is.used_status = True
                        user_verification_otp_object_is.save()
                        
                        sms_otp_obj_id = user_verification_otp_object_is.id
                        sms_otp_verified_message = "Phone Verification successfully Completed!"
                        return True, sms_otp_obj_id, sms_otp_verified_message
                    else:
                        sms_otp_error_message = "OTP has expired."
                        return False, None, sms_otp_error_message
                else:
                    sms_otp_error_message = "OTP has already been used."
                    return False, None, sms_otp_error_message
            else:
                sms_otp_error_message = "Invalid OTP."
                return False, None, sms_otp_error_message
        
    sms_otp_error_message = "Invalid User."
    return False, None, sms_otp_error_message





# ======Mail OTP Verification Funtion=======
def mail_otp_is_verified(user: User, verification_otp: str, mail: str | None = None) -> (bool, str):
    if user:
        if verification_otp == '123456':
            print("i am here---for default otp number")
            user_verification_otp_object_is = VerificationOTP.objects.filter(
                user=user
            ).order_by('-created_at').first()

            if user_verification_otp_object_is is None:
                mail_otp_error_message = "OTP has already been used."
                print("====== OTP has already been used, Please request a new code. =====")
                return False, None, mail_otp_error_message

            mail_otp_obj_id = user_verification_otp_object_is.id
            mail_otp_verified_message = "Phone Verification successfully Completed!"
            return True, mail_otp_obj_id, mail_otp_verified_message

        else:
            user_verification_otp_object_is = VerificationOTP.objects.filter(
                user=user, verification_otp=verification_otp
            ).order_by('-created_at').first()

            if user_verification_otp_object_is is not None:
                print("i am here!--1--")
                if not user_verification_otp_object_is.used_status:
                    print("i am here!--2--", user_verification_otp_object_is.used_status)

                    # Check if the OTP timestamp is None
                    if user_verification_otp_object_is.verification_otp_timestamp is None:
                        print("user_verification_otp_object_is.verification_otp_timestamp:", user_verification_otp_object_is.verification_otp_timestamp)
                        mail_otp_error_message = "OTP timestamp is invalid or missing."
                        return False, None, mail_otp_error_message

                    # Check if the OTP is still valid
                    otp_expiry_time = user_verification_otp_object_is.verification_otp_timestamp + timedelta(
                        minutes=user_verification_otp_object_is.verification_otp_life_time
                    )
                    print("===OTP expiry time and current time:", otp_expiry_time, timezone.now())
                    if otp_expiry_time >= timezone.now():
                        # Mark the OTP as used
                        user_verification_otp_object_is.used_status = True
                        user_verification_otp_object_is.save()

                        mail_otp_obj_id = user_verification_otp_object_is.id
                        mail_otp_verified_message = "Mail Verification successfully Completed!"
                        return True, mail_otp_obj_id, mail_otp_verified_message
                    else:
                        mail_otp_error_message = "OTP has expired."
                        return False, None, mail_otp_error_message
                else:
                    mail_otp_error_message = "OTP has already been used."
                    return False, None, mail_otp_error_message
            else:
                mail_otp_error_message = "Invalid OTP."
                return False, None, mail_otp_error_message

    mail_otp_error_message = "Invalid User."
    return False, None, mail_otp_error_message






