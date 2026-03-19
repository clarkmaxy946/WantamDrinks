# payments/services.py
import base64
import requests
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Payment
from orders.models import Order
from orders.services import confirm_order, restore_order_stock




def get_mpesa_access_token():
    
    try:
        response = requests.get(
            settings.MPESA_AUTH_URL,    # URL from settings — swap sandbox/live there
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=30
        )
        response.raise_for_status()
        return response.json()['access_token']

    except requests.exceptions.Timeout:
        raise ValidationError("M-Pesa authentication timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise ValidationError(f"M-Pesa authentication failed: {str(e)}")


def generate_stk_password():
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(raw.encode()).decode('utf-8')
    return password, timestamp


def format_phone_number(phone_number):
    
    return f"254{phone_number[1:]}"


def initiate_stk_push(order, phone_number):
    
    if order.status != Order.Status.PENDING:
        raise ValidationError(
            f"Order {order.order_id} is {order.status}. "
            f"Only PENDING orders can be paid."
        )

    # Prevent double payment
    if hasattr(order, 'payment'):
        existing = order.payment
        if existing.status == Payment.Status.SUCCESS:
            raise ValidationError(
                f"Order {order.order_id} has already been paid successfully."
            )
        if existing.status == Payment.Status.PENDING:
            raise ValidationError(
                f"A payment for order {order.order_id} is already in progress. "
                f"Please wait for the M-Pesa prompt."
            )

    
    access_token = get_mpesa_access_token()

    
    password, timestamp = generate_stk_password()

    
    formatted_phone = format_phone_number(phone_number)

    
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(order.total_price),
        "PartyA": formatted_phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": order.order_id,
        "TransactionDesc": f"Payment for WantamDrinks Order {order.order_id}"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    
    try:
        response = requests.post(
            settings.MPESA_STK_URL,     # URL from settings — swap sandbox/live there
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        response_data = response.json()

    except requests.exceptions.Timeout:
        raise ValidationError("M-Pesa request timed out. Please try again.")
    except requests.exceptions.RequestException as e:
        raise ValidationError(f"M-Pesa request failed: {str(e)}")

    
    if response_data.get('ResponseCode') != '0':
        raise ValidationError(
            f"M-Pesa rejected the request: "
            f"{response_data.get('ResponseDescription', 'Unknown error')}"
        )

    
    payment = Payment.objects.create(
        order=order,
        user=order.user,
        phone_number=phone_number,
        amount=order.total_price,
        checkout_request_id=response_data['CheckoutRequestID'],
        merchant_request_id=response_data['MerchantRequestID'],
        status=Payment.Status.PENDING
    )

    return payment




def process_mpesa_callback(callback_data):
    
    try:
        stk_callback = callback_data['Body']['stkCallback']
        checkout_request_id = stk_callback['CheckoutRequestID']
        result_code = stk_callback['ResultCode']
    except KeyError:
        
        return None

    
    try:
        payment = Payment.objects.get(checkout_request_id=checkout_request_id)
    except Payment.DoesNotExist:
       
        return None

    
    if payment.status != Payment.Status.PENDING:
        return payment

    
    if result_code == 0:
        return _handle_successful_payment(payment, stk_callback)
    else:
        return _handle_failed_payment(payment, stk_callback, result_code)




def _handle_successful_payment(payment, stk_callback):
    
    metadata = {}
    items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
    for item in items:
        if 'Value' in item:
            metadata[item['Name']] = item['Value']

    receipt_number = metadata.get('MpesaReceiptNumber')
    paid_amount = metadata.get('Amount')

    
    if paid_amount and float(paid_amount) != float(payment.order.total_price):
        return _handle_failed_payment(
            payment,
            stk_callback,
            result_code=99,
            override_desc=(
                f"Amount mismatch. "
                f"Expected KES {payment.order.total_price}, "
                f"received KES {paid_amount}."
            )
        )

    with transaction.atomic():

        
        payment.status = Payment.Status.SUCCESS
        payment.receipt_number = receipt_number
        payment.raw_callback = stk_callback
        payment.save()

        
        confirm_order(payment.order, receipt_number)

    return payment




def _handle_failed_payment(payment, stk_callback, result_code, override_desc=None):
    
    failure_reasons = {
        1:    "Insufficient funds",
        17:   "M-Pesa limit reached",
        1032: "Request cancelled by user",
        1037: "Request timed out",
        2001: "Invalid M-Pesa PIN",
    }

    
    mapped_reason = (
        override_desc
        or failure_reasons.get(result_code, f"Payment failed (Code: {result_code})")
    )

    
    safaricom_desc = stk_callback.get('ResultDesc', '')

    
    full_reason = f"{mapped_reason} | Safaricom: {safaricom_desc}".strip(' |')

    with transaction.atomic():

        # Update payment to FAILED
        payment.status = Payment.Status.FAILED
        payment.failure_reason = full_reason
        payment.raw_callback = stk_callback
        payment.save()
        
        restore_order_stock(payment.order)  

        # Update order to FAILED
        order = payment.order
        order.status = Order.Status.FAILED
        order.save()

    return payment