from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/phone/', views.SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('auth/verify/', views.VerifyCodeView.as_view(), name='verify-code'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('invite/activate/', views.ActivateInviteCodeView.as_view(), name='activate-invite'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]