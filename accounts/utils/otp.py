from django.conf import settings
from accounts.models import OtpTypes, VerificationOTP
import random
from django.contrib.auth import get_user_model
User = get_user_model()


# Generate OTP ==================
def generate_otp() -> str:
    return str(random.randint(100000, 999999))

      
# ============== OTP Send Funtion======================    
def otp_send(user: User | None = None) -> None:
    if user:
        phone_number = (user.phone_number) 
        otp = generate_otp()

        try:
            account_sid = 'AC1d58e90bd49522bc82bf5827dbdfcff7'
            auth_token = 'ec1f047b24ba931075f9d9ee4a6040fb'
            message_sid = "message.sid" # message SID
            return otp,message_sid
            
        except Exception as e:
            print("There was a problem.")
            print(e)
            return None,None
    else:
        print("No user provided.")
        return None,None
        




