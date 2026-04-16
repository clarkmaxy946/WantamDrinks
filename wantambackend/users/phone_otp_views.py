"""
users/phone_otp_views.py

Two endpoints that handle phone-number change via email OTP.

Flow:
  1. POST /auth/phone-change/request-otp/
       - Accepts { "new_phone": "07XXXXXXXX" }
       - Validates format + uniqueness
       - Generates a 6-digit OTP, stores it in the session (TTL 10 min)
       - Emails it to the user's registered address via Django's send_mail
       - Returns 200 with a generic "OTP sent" message

  2. POST /auth/phone-change/verify-otp/
       - Accepts { "new_phone": "07XXXXXXXX", "otp": "123456" }
       - Verifies the OTP from session (checks code + expiry + phone match)
       - On success: updates user.phone_number and clears the session key
       - Returns 200 with updated profile data

Session key used: "phone_change_otp"
Session value structure:
  {
    "code":      "123456",
    "new_phone": "0712345678",
    "expires_at": 1714000000.0   # time.time() + 600
  }
"""

import random
import time
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser

logger = logging.getLogger(__name__)

# ── Shared phone validator (mirrors the one on the model) ──────────────────────
_phone_re = RegexValidator(
    regex=r'^(07|01)\d{8}$',
    message="Phone number must be 10 digits starting with 07 or 01.",
)

OTP_TTL_SECONDS = 600          # 10 minutes
SESSION_KEY     = "phone_change_otp"


def _validate_phone(value: str) -> str:
    """Run the regex validator and return the cleaned value, or raise."""
    try:
        _phone_re(value)
    except DjangoValidationError as exc:
        raise exc
    return value


def _generate_otp() -> str:
    """Return a zero-padded 6-digit string."""
    return f"{random.SystemRandom().randint(0, 999999):06d}"


# ── VIEW 1 — Request OTP ───────────────────────────────────────────────────────

class PhoneChangeRequestOTPView(APIView):
    """
    POST /auth/phone-change/request-otp/
    Body: { "new_phone": "0712345678" }

    Authenticated users only.
    Rate-limiting note: consider pairing this with django-ratelimit in production.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_phone = (request.data.get("new_phone") or "").strip()

        # ── 1. Presence check ─────────────────────────────────────────────────
        if not new_phone:
            return Response(
                {"error": "new_phone is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 2. Format validation ──────────────────────────────────────────────
        try:
            _validate_phone(new_phone)
        except DjangoValidationError as exc:
            return Response(
                {"error": exc.message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 3. Uniqueness check (exclude self) ────────────────────────────────
        if (
            CustomUser.objects
            .filter(phone_number=new_phone)
            .exclude(pk=request.user.pk)
            .exists()
        ):
            return Response(
                {"error": "This phone number is already in use by another account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 4. Guard: no-op if same as current ───────────────────────────────
        if request.user.phone_number == new_phone:
            return Response(
                {"error": "This is already your registered phone number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 5. Generate OTP and persist in session ────────────────────────────
        otp = _generate_otp()
        request.session[SESSION_KEY] = {
            "code":       otp,
            "new_phone":  new_phone,
            "expires_at": time.time() + OTP_TTL_SECONDS,
        }
        request.session.modified = True

        # ── 6. Send email ─────────────────────────────────────────────────────
        try:
            send_mail(
                subject="Your WantamDrinks phone-change verification code",
                message=(
                    f"Hi {request.user.username},\n\n"
                    f"Your one-time verification code to change your phone number is:\n\n"
                    f"    {otp}\n\n"
                    f"This code expires in 10 minutes.\n\n"
                    f"If you did not request this, please ignore this email — "
                    f"your account has not been changed.\n\n"
                    f"— WantamDrinks Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send phone-change OTP email to %s", request.user.email)
            # Clear the session entry so the user can retry cleanly
            request.session.pop(SESSION_KEY, None)
            return Response(
                {"error": "Failed to send verification email. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": (
                    f"A 6-digit verification code has been sent to "
                    f"{request.user.email}. It expires in 10 minutes."
                )
            },
            status=status.HTTP_200_OK,
        )


# ── VIEW 2 — Verify OTP & Apply Change ────────────────────────────────────────

class PhoneChangeVerifyOTPView(APIView):
    """
    POST /auth/phone-change/verify-otp/
    Body: { "new_phone": "0712345678", "otp": "123456" }

    Authenticated users only.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        new_phone = (request.data.get("new_phone") or "").strip()
        submitted = (request.data.get("otp")       or "").strip()

        # ── 1. Basic presence ─────────────────────────────────────────────────
        if not new_phone or not submitted:
            return Response(
                {"error": "Both new_phone and otp are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 2. Session lookup ─────────────────────────────────────────────────
        stored = request.session.get(SESSION_KEY)
        if not stored:
            return Response(
                {"error": "No pending phone-change request found. Please request a new code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 3. Expiry check ───────────────────────────────────────────────────
        if time.time() > stored.get("expires_at", 0):
            request.session.pop(SESSION_KEY, None)
            return Response(
                {"error": "Verification code has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 4. Phone-match check (OTP is bound to a specific number) ──────────
        if stored.get("new_phone") != new_phone:
            return Response(
                {"error": "Phone number does not match the pending request."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 5. Code check ─────────────────────────────────────────────────────
        if stored.get("code") != submitted:
            return Response(
                {"error": "Incorrect verification code. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 6. Re-validate uniqueness (race-condition guard) ──────────────────
        if (
            CustomUser.objects
            .filter(phone_number=new_phone)
            .exclude(pk=request.user.pk)
            .exists()
        ):
            request.session.pop(SESSION_KEY, None)
            return Response(
                {"error": "This phone number was taken by another account. Please choose a different number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── 7. Apply change ───────────────────────────────────────────────────
        request.user.phone_number = new_phone
        request.user.save(update_fields=["phone_number"])

        # Invalidate the OTP so it cannot be reused
        request.session.pop(SESSION_KEY, None)

        return Response(
            {
                "message": "Phone number updated successfully.",
                "phone_number": new_phone,
            },
            status=status.HTTP_200_OK,
        )