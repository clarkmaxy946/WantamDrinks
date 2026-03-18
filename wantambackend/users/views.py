# users/views.py
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
)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Public — no token required.
    Creates account and returns JWT tokens immediately.
    User does not need to login separately after registration.
    """
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
    """
    POST /api/auth/login/
    Public — no token required.
    Authenticates with email + password.
    Returns JWT access and refresh tokens.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class ProfileView(APIView):
    """
    GET   /api/auth/profile/ → view own profile
    PATCH /api/auth/profile/ → update username or phone
    Protected — requires JWT token.
    """
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
    """
    GET /api/admin/users/
    Admin only — requires is_staff=True.
    Returns all registered users with total order count.
    No select_related needed — no related model on CustomUser.
    """
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
    """
    GET    /api/admin/users/<user_id>/ → view single user
    PATCH  /api/admin/users/<user_id>/ → deactivate/reactivate
    DELETE /api/admin/users/<user_id>/ → delete user
    Admin only — requires is_staff=True.
    """
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