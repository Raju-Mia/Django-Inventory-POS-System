from django.urls import path


from accounts.view.views import (
    CustomTokenObtainPairView, 
    CustomTokenRefreshView, 
    UserSignUpView, 
    UserLoginView, 
    UserLogoutView,
    OTPVerificationView, 
    ResendOTPView, 
    UserForgetPasswordView, 
    VerifyForgotPasswordOTP,
    ChangeForgetPassword,
    UserChangePasswordView, 
    UserUpdateProfileView, 
    UserDeleteProfilePictureView, 
    UserProfileDetailView
    )

from accounts.view.operator_views import (
    OperatorCreateAPIView,
    OperatorListAPIView,
    OperatorDetailAPIView,
    OperatorDeleteAPIView,
)



urlpatterns = [
    # Access token (Login)
    path('access-token/', CustomTokenObtainPairView.as_view()),

    # Custom Refresh token
    path('refresh-token/', CustomTokenRefreshView.as_view()), 
    
    # ------------------ User ------------------
    path('user-login/', UserLoginView.as_view(), name='user-login'),
    path('user-logout/', UserLogoutView.as_view(), name='user-logout'),
    path('user-signup/', UserSignUpView.as_view(), name='user-signup'),
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),     

    path('forget-password/', UserForgetPasswordView.as_view(), name='forget-password'),
    path("password-forgot/otp-verify/",VerifyForgotPasswordOTP.as_view()),
    path("password-forgot/new-password-set/",ChangeForgetPassword.as_view()),
    
    path('change-password/', UserChangePasswordView.as_view(), name='change-password'),
    path('update-profile/', UserUpdateProfileView.as_view(), name='update-profile'),
    path('user-profile/', UserProfileDetailView.as_view(), name='user-profile-detail'),
    path('delete-profile-picture/', UserDeleteProfilePictureView.as_view(), name='delete-profile-picture'),
    
    
    #-------------------- Operator --------------------------
    path("v1/operators/create/", OperatorCreateAPIView.as_view(), name="operator-create"),
    path("v1/operators/", OperatorListAPIView.as_view(), name="operator-list"),
    path("v1/operators/<str:user_id>/", OperatorDetailAPIView.as_view(), name="operator-detail"),
    path("v1/operators/<str:user_id>/delete/", OperatorDeleteAPIView.as_view(), name="operator-delete"),

]