# users/views.py
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count
from .models import CustomUser
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
)


class RegisterView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate tokens immediately — no separate login needed
            refresh = RefreshToken.for_user(user)
            refresh['wnt_id'] = user.user_id
            refresh['email'] = user.email
            refresh['is_staff'] = user.is_staff

            return Response(
                {
                    "message": "Account created successfully.",
                    "user_id": user.user_id,
                    "email": user.email,
                    "username": user.username,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginView(TokenObtainPairView):
    
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class ProfileView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        serializer = UpdateProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Profile updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminUserListView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = CustomUser.objects.annotate(
            total_orders=Count('orders')
        ).order_by('-created_at')

        serializer = AdminUserListSerializer(users, many=True)
        return Response(
            {
                "total_users": users.count(),
                "users": serializer.data
            },
            status=status.HTTP_200_OK
        )




class AdminUserDetailView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            return None

    def get(self, request, user_id):
        user = self.get_user(user_id)
        if not user:
            return Response(
                {"error": f"User {user_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminUserDetailSerializer(user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, user_id):
        user = self.get_user(user_id)
        if not user:
            return Response(
                {"error": f"User {user_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminUserDetailSerializer(
            user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": f"User {user_id} updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, user_id):
        user = self.get_user(user_id)
        if not user:
            return Response(
                {"error": f"User {user_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if user == request.user:
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.delete()
        return Response(
            {"message": f"User {user_id} deleted successfully."},
            status=status.HTTP_200_OK
        )
        
        
class PasswordChangeView(APIView):
    """
    PUT /auth/change-password/
    Body: { "current_password": "...", "new_password": "...", "confirm_password": "..." }
 
    Allows an authenticated user to change their own password.
    Requires current password as proof of identity.
    Runs full AUTH_PASSWORD_VALIDATORS chain including WantamPasswordValidator.
    """
 
    permission_classes = [IsAuthenticated]
 
    def put(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )        
        
        
 
class PasswordResetRequestView(APIView):
    """
    POST /auth/forgot-password/
    Body: { "email": "user@example.com" }
 
    Generates a signed one-time token and emails the reset link.
    Always returns 200 to prevent email enumeration.
    """
 
    permission_classes = [AllowAny]
 
    def post(self, request):
        email = request.data.get("email", "").strip().lower()
 
        if not email:
            return Response(
                {"error": "Email address is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        try:
            user = CustomUser.objects.get(email__iexact=email)
 
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
 
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            reset_link   = f"{frontend_url}/reset-password/{uid}/{token}/"
 
            send_mail(
                subject="Reset your password",
                message=(
                    f"Hi {user.username},\n\n"
                    f"Click the link below to reset your password.\n"
                    f"This link expires in 3 days.\n\n"
                    f"{reset_link}\n\n"
                    f"If you did not request this, you can safely ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
 
        except CustomUser.DoesNotExist:
            pass  # Intentional — same response either way
 
        return Response(
            {"message": "If that email is registered, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )
 
 
class PasswordResetConfirmView(APIView):
    """
    POST /auth/reset-password/<uidb64>/<token>/
    Body: { "new_password": "...", "confirm_password": "..." }
 
    Validates token then delegates all password rules to
    PasswordResetConfirmSerializer (runs full AUTH_PASSWORD_VALIDATORS).
    Token is single-use — invalidated once password changes.
    """
 
    permission_classes = [AllowAny]
 
    def post(self, request, uidb64, token):
 
        # ── Serializer handles all password validation ──────────────────────
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # ── Decode the uid — view's responsibility, not serializer's ────────
        try:
            uid  = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response(
                {"error": "Reset link is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # ── Validate token signature and expiry ─────────────────────────────
        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Reset link has expired or already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        # ── All good — update the password ──────────────────────────────────
        user.set_password(serializer.validated_data['new_password'])
        user.save()
 
        return Response(
            {"message": "Password reset successful. You can now log in."},
            status=status.HTTP_200_OK,
        )
        