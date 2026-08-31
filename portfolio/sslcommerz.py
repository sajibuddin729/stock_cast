import requests
import urllib3
import logging
from django.conf import settings

# Disable SSL Warnings for Sandbox environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

def initiate_sslcommerz_session(transaction, user, success_url, fail_url, cancel_url):
    """
    SSLCommerz v4 Session API Call for Sandbox & Live.
    Returns: {"status": "SUCCESS", "gateway_url": "https://...", "tran_id": tran_id}
    """
    post_body = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASS,
        'total_amount': str(transaction.amount_bdt),
        'currency': 'BDT',
        'tran_id': transaction.tran_id,
        'success_url': success_url,
        'fail_url': fail_url,
        'cancel_url': cancel_url,
        'emi_option': '0',
        'cus_name': user.first_name or user.username,
        'cus_email': user.email or f"{user.username}@stockcast.app",
        'cus_add1': 'Dhaka, Bangladesh',
        'cus_city': 'Dhaka',
        'cus_postcode': '1200',
        'cus_country': 'Bangladesh',
        'cus_phone': transaction.account_number or '01700000000',
        'shipping_method': 'NO',
        'product_name': 'StockCast Wallet Deposit',
        'product_category': 'Fintech Wallet',
        'product_profile': 'general',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.post(
            settings.SSLCOMMERZ_SESSION_API,
            data=post_body,
            headers=headers,
            timeout=10,
            verify=False
        )
        res_data = response.json()
        if res_data.get('status') == 'SUCCESS' and 'GatewayPageURL' in res_data:
            return {
                'status': 'SUCCESS',
                'gateway_url': res_data['GatewayPageURL'],
                'session_key': res_data.get('sessionkey'),
                'tran_id': transaction.tran_id,
            }
        else:
            logger.error(f"SSLCommerz API failed: {res_data.get('failedreason')}")
    except Exception as e:
        logger.warning(f"SSLCommerz Remote Server Timeout/Error ({e}).")

    # Seamless Sandbox Checkout URL for testing & development
    if settings.SSLCOMMERZ_IS_SANDBOX:
        mock_gateway_url = f"https://sandbox.sslcommerz.com/EasyCheckOut/{transaction.tran_id}"
        return {
            'status': 'SUCCESS',
            'gateway_url': mock_gateway_url,
            'session_key': f"SESS_{transaction.tran_id}",
            'tran_id': transaction.tran_id,
        }

    return {
        'status': 'FAILED',
        'failed_reason': 'SSLCommerz gateway connection failed. Please try again.'
    }

def validate_sslcommerz_payment(val_id):
    """
    Validates transaction against SSLCommerz API Server.
    """
    params = {
        'val_id': val_id,
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_pass': settings.SSLCOMMERZ_STORE_PASS,
        'format': 'json',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    try:
        res = requests.get(
            settings.SSLCOMMERZ_VALIDATION_API,
            params=params,
            headers=headers,
            timeout=3,
            verify=False
        )
        return res.json()
    except Exception as e:
        logger.error(f"SSLCommerz Validation Error: {e}")
        return None
