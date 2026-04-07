# users/serializers.py — final complete version
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles new customer registration.
    - Validates email uniqueness and gmail format (via model validator)
    - Validates Kenyan phone format 07/01 (via model validator)
    - Hashes password using create_user()
    - Runs WantamPasswordValidator rules via validate_password()
    - Auto-generates WNT-ID via model save()
    - Always creates regular user — is_staff=False
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'phone_number',
            'password',
            'confirm_password',
        ]

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "A user with this phone number already exists."
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })

        # Runs ALL validators in AUTH_PASSWORD_VALIDATORS
        # including your WantamPasswordValidator
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        # create_user() hashes password automatically
        # Never use .create() directly — stores plain text
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            is_staff=False,
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """
    Handles login via email + password.
    Returns JWT access and refresh tokens.
    Adds custom fields to JWT payload.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims embedded in JWT payload
        token['wnt_id'] = user.user_id
        token['email'] = user.email
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Extra fields in login response body
        data['wnt_id'] = self.user.user_id
        data['email'] = self.user.email
        data['username'] = self.user.username
        data['is_staff'] = self.user.is_staff
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read-only profile for authenticated customer.
    Shield — only safe fields exposed.
    Password, permissions, groups never included.
    """

    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'username',
            'email',
            'phone_number',
            'is_staff',
            'created_at',
        ]
        read_only_fields = [
            'user_id',
            'email',
            'is_staff',
            'created_at',
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    """
    Allows customer to update username and phone only.
    Email is permanent — cannot be changed.
    Password changes handled by separate endpoint.
    """

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'phone_number',
        ]

    def validate_phone_number(self, value):
        user = self.context['request'].user
        if CustomUser.objects.filter(
            phone_number=value
        ).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "This phone number is already in use."
            )
        return value


class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Admin-only — full user list with order count.
    total_orders is annotated in the view using Count().
    """

    # Annotated in the view — not a model field
    total_orders = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'username',
            'email',
            'phone_number',
            'is_staff',
            'is_active',
            'created_at',
            'total_orders',
        ]
        read_only_fields = [
            'user_id',
            'email',
            'created_at',
            'total_orders',
            'is_staff',
        ]


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """
    Admin-only — single user management.
    Admin can deactivate/reactivate accounts via is_active.
    Deactivation preserves all data and order history.
    """

    class Meta:
        model = CustomUser
        fields = [
            'user_id',
            'username',
            'email',
            'phone_number',
            'is_staff',
            'is_active',
            'created_at',
        ]
        read_only_fields = [
            'user_id',
            'email',
            'created_at',
            'is_staff',
        ]