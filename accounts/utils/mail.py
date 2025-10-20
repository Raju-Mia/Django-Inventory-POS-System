import requests
from django.conf import settings

from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives

from accounts.utils.otp import generate_otp
from accounts.models import Organization, CustomUser, OtpTypes, VerificationOTP, VerificationTokens, TokenTypes
from django.contrib.auth import get_user_model
User = get_user_model()


# Send Mail-- New Updated Code 
def send_mail(payload: dict) -> bool:
    email = payload['recipient_list']
    mail_type = payload['mail_type']

    print("==============payload===========: ", payload)
    
    # Determine HTML template based on mail type
    if mail_type == 'registration':
        subject = 'Invitation For Registration'
        html_template = "accounts/mail/registration.html"
        
    elif mail_type == 'login_reds':
        subject = 'Account Login Credentials'
        html_template = "accounts/mail/login-creds.html"
        
    elif mail_type == 'password_change':
        subject = 'Password Change OTP'
        html_template = "accounts/mail/password-change.html"

    elif mail_type == 'password_reset':
        subject = 'Password Forgot OTP'
        html_template = "accounts/mail/password-forgot.html"

        
    elif mail_type == 'mail_verification':
        subject = 'Mail Verification'
        html_template = "accounts/mail/email-verification.html"
        
        
    elif mail_type == 'resend_otp':
        subject = 'Resend OTP'
        html_template = "accounts/mail/resend-otp.html"
        
        
    else:
        subject = 'Welcome to PIMS Word!'
        print("Invalid mail type.")
        return False

    # Render the HTML template with the context data
    html_content = render_to_string(html_template, payload)

    # Send email
    from_email = settings.DEFAULT_FROM_EMAIL  # Your from email

    
    # Determine recipient email(s)
    if isinstance(email, list): 
        to_email = email[0]  # Use the first email address if it's a list

    elif isinstance(email, str):
        to_email = email  # Use the email address directly if it's a string

    else:
        print("Invalid email format.")
        return False
    
    # Create the email message object
    msg = EmailMultiAlternatives(subject, '', from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")  # Attach HTML content
    
    try:
        msg.send()
        return True
    except Exception as e:
        print(str(e))
        return False
    
    
    
    



# Function to send email verification token
def send_email_verification_token(user: User, email: str | None = None, name: str = None, username: str = None, password: str = None) -> None:
    """
    Sends verification email to the user's mail address when a new user is created.
    """

    # Create a verification token
    token = VerificationTokens.objects.create(
        user=user, token_type=TokenTypes.email_verification, token=generate_otp()
    )
    

    url = (
        settings.URL_TO_SEND_EMAIL_VERIFICATION_URL
        + "service="
        + user.service
        + "&user_id="
        + str(user.id)
        + "&token="
        + token.token
    )

    # Prepare the email payload
    payload = {
        "recipient_list": [email] if email else [user.email],
        "url": url,
        "code": token.token,
        "mail_type": "mail verification",
        "name": name,
        "username": username,
        "email":email,
        "password": password,
    }

     # Send the verification email
    success = send_mail(payload)
    
    if success:
        print(f"Verification email sent to {user.email}")
    else:
        print(f"Failed to send verification email to {user.email}")





def send_otp_mail(user: User) -> None:
    otp = VerificationOTP.objects.create(
        user=user, otp_type=OtpTypes.email_verification, verification_otp=generate_otp(), verification_otp_timestamp=timezone.now()
    )

            
    payload = {
        "recipient_list": [user.email],
        "code": otp.verification_otp,
        "mail_type": "mail_verification",
        }
    send_mail(payload)
    
    

def resend_otp_mail(user: User) -> None:
    otp = VerificationOTP.objects.create(
        user=user, otp_type=OtpTypes.email_verification, verification_otp=generate_otp(), verification_otp_timestamp=timezone.now()
    )

            
    payload = {
        "recipient_list": [user.email],
        "code": otp.verification_otp,
        "mail_type": "resend_otp",
        }
    send_mail(payload)
    
    

def send_reset_otp_mail(user: User) -> None:
    otp = VerificationOTP.objects.create(
        user=user, otp_type=OtpTypes.password_reset, verification_otp=generate_otp(), verification_otp_timestamp=timezone.now()
    )
    payload = {
        "recipient_list": [user.email],
        "code": otp.verification_otp,
        "mail_type": "password_reset",
    }
    send_mail(payload)










