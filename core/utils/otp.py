from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import OtpTypes, VerificationOTP
import random
User = get_user_model()





# Generate OTP ==================
def generate_otp() -> str:
    return str(random.randint(100000, 999999))



      
# ============== OTP Send Funtion======================    
def otp_send(user: User | None = None) -> None:
    if user:
        phone_number = (user.phone)  # Keeping phone number as string for Twilio compatibility
        otp = generate_otp()

        try:
            message_sid = "message.sid" # message SID
            return otp,message_sid
            
        except Exception as e:
            print("There was a problem.")
            print(e)
            return None,None
    else:
        print("No user provided.")
        return None,None
        




