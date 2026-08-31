import time
import decimal
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Watchlist, Transaction, UserProfile, WalletTransaction
from .serializers import (
    RegisterSerializer,
    WatchlistSerializer,
    TransactionSerializer,
    UserProfileSerializer,
    WalletTransactionSerializer,
)
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.db.models import Q

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Dual Login Serializer: Allows users to log in using EITHER Email OR Username seamlessly!
    """
    def validate(self, attrs):
        username_or_email = attrs.get('username', '').strip()
        if username_or_email:
            user = User.objects.filter(
                Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
            ).first()
            if user:
                attrs['username'] = user.username
        return super().validate(attrs)

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(APIView):
    """
    নতুন ইউজার রেজিস্ট্রেশন (Create Account) API.
    Input: name, email, password, confirm_password (username optional)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Account created successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "name": user.first_name,
                    "email": user.email,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response({
            "profile": serializer.data,
            "username": request.user.username,
            "name": request.user.first_name,
            "email": request.user.email
        })

class WatchlistView(generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WatchlistDeleteView(generics.DestroyAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user).order_by('-timestamp')
        tx_type = self.request.query_params.get('type')
        if tx_type and tx_type.upper() in ['BUY', 'SELL']:
            qs = qs.filter(transaction_type=tx_type.upper())
        return qs

    def perform_create(self, serializer):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        total_cost = serializer.validated_data['quantity'] * serializer.validated_data['price_per_share']

        if serializer.validated_data['transaction_type'] == 'BUY':
            profile.current_balance -= total_cost
        else:
            profile.current_balance += total_cost

        profile.save()
        serializer.save(user=self.request.user)


# ── MY ALL HISTORY & PORTFOLIO HOLDINGS OVERVIEW API ──────────────────────────

class PortfolioHistoryOverviewView(APIView):
    """
    My All History Screen Overview API.
    Calculates:
    - 30-Day Activity Overview (Total Bought $, Total Sold $, Active Holdings Count)
    - Available Shares Inventory (Holdings with Avg Buy Price, Latest Price, Current Value)
    - Total Current Inventory Value
    - Buys count & Sells count
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        txs = Transaction.objects.filter(user=user).select_related('stock')

        # 1. Total Bought
        buy_txs = txs.filter(transaction_type='BUY')
        total_bought_val = sum(tx.quantity * tx.price_per_share for tx in buy_txs)
        total_bought_qty = sum(tx.quantity for tx in buy_txs)

        # 2. Total Sold
        sell_txs = txs.filter(transaction_type='SELL')
        total_sold_val = sum(tx.quantity * tx.price_per_share for tx in sell_txs)
        total_sold_qty = sum(tx.quantity for tx in sell_txs)

        # 3. Calculate Holdings per stock
        stock_map = {}
        for tx in txs.order_by('timestamp'):
            sid = tx.stock.id
            if sid not in stock_map:
                stock_map[sid] = {
                    'stock': tx.stock,
                    'qty': 0,
                    'total_spent': decimal.Decimal('0.00'),
                }
            if tx.transaction_type == 'BUY':
                stock_map[sid]['qty'] += tx.quantity
                stock_map[sid]['total_spent'] += (tx.quantity * tx.price_per_share)
            else:
                stock_map[sid]['qty'] -= tx.quantity

        holdings_list = []
        total_inventory_val = decimal.Decimal('0.00')

        for sid, data in stock_map.items():
            qty = data['qty']
            if qty > 0:
                stk = data['stock']
                last_price_obj = stk.prices.order_by('-timestamp').first()
                if last_price_obj and last_price_obj.close_price:
                    latest_p = decimal.Decimal(str(last_price_obj.close_price))
                else:
                    latest_p = decimal.Decimal('100.00')

                avg_buy_p = data['total_spent'] / qty if qty > 0 else decimal.Decimal('0.00')
                curr_val = qty * latest_p
                total_inventory_val += curr_val

                is_dse = (stk.market_type == 'DSE')
                currency = '৳' if is_dse else '$'

                holdings_list.append({
                    'stock_id': stk.id,
                    'symbol': stk.symbol,
                    'name': stk.name or f"{stk.symbol} Stock",
                    'market_type': stk.market_type,
                    'is_dse': is_dse,
                    'currency_symbol': currency,
                    'quantity': qty,
                    'avg_buy_price': float(round(avg_buy_p, 2)),
                    'latest_market_price': float(round(latest_p, 2)),
                    'current_value': float(round(curr_val, 2)),
                })

        return Response({
            "activity_overview": {
                "total_bought_val": float(round(total_bought_val, 2)),
                "total_bought_qty": total_bought_qty,
                "total_sold_val": float(round(total_sold_val, 2)),
                "total_sold_qty": total_sold_qty,
                "active_holdings_count": len(holdings_list),
            },
            "holdings_summary": {
                "total_inventory_value": float(round(total_inventory_val, 2)),
                "unique_stocks_count": len(holdings_list),
            },
            "holdings": holdings_list,
            "counts": {
                "holdings_count": len(holdings_list),
                "buys_count": buy_txs.count(),
                "sells_count": sell_txs.count(),
            }
        })


# ── WALLET & PAYMENT GATEWAY (SSLCOMMERZ + 1% FEE LOGIC) ───────────────────────

class WalletTransactionListCreateView(APIView):
    """
    ক্যাশ ইন (Cash In) ও উইথড্র (Withdrawal) এর জন্য ডাইরেক্ট ওয়ালেট ট্রানজ্যাকশন API।
    - Cash In: 0% fee (ডিপোজিট ফ্রিতে পুরো টাকা ওয়ালেটে যুক্ত হবে)
    - Withdraw: 1.00% অ্যাপ ফি কাটা হবে এবং অবশিষ্ট ইউজারের পেমেন্ট মেথডে যাবে।
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        txs = WalletTransaction.objects.filter(user=request.user).order_by('-created_at')
        serializer = WalletTransactionSerializer(txs, many=True)
        return Response(serializer.data)

    def post(self, request):
        tx_type = request.data.get('transaction_type', 'CASH_IN').upper()
        amount_str = request.data.get('amount', '0')
        payment_method = request.data.get('payment_method', 'bKash')
        account_number = request.data.get('account_number', '')
        reference_note = request.data.get('reference_note', 'StockCast Wallet Transaction')

        try:
            gross_amount = decimal.Decimal(str(amount_str))
            if gross_amount <= 0:
                return Response({"error": "Amount must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, decimal.InvalidOperation):
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        tran_id = f"STKCAST_{tx_type}_{int(time.time())}_{request.user.id}"

        # 1. CASH IN / DEPOSIT (Strict 1.00% Fee Deduction)
        if tx_type == 'CASH_IN':
            fee_percentage = decimal.Decimal(str(settings.CASH_IN_FEE_PERCENT))  # 1.00%
            fee_amount = (gross_amount * fee_percentage) / decimal.Decimal('100.00')
            net_amount = gross_amount - fee_amount
            amount_bdt = gross_amount * decimal.Decimal(str(settings.USD_TO_BDT_RATE))

            # Update User Balance with Net Amount (after 1% fee)
            profile.current_balance += net_amount
            profile.save()

            wallet_tx = WalletTransaction.objects.create(
                user=request.user,
                transaction_type='CASH_IN',
                payment_method=payment_method,
                tran_id=tran_id,
                gross_amount=gross_amount,
                fee_percentage=fee_percentage,
                fee_amount=fee_amount,
                net_amount=net_amount,
                amount_bdt=amount_bdt,
                status='COMPLETED',
                account_number=account_number,
                reference_note=reference_note
            )

            return Response({
                "message": f"Successfully deposited ${net_amount:.2f} into wallet (1% Fee: ${fee_amount:.2f}).",
                "new_balance": float(profile.current_balance),
                "transaction": WalletTransactionSerializer(wallet_tx).data
            }, status=status.HTTP_201_CREATED)

        # 2. WITHDRAWAL (Strict 1.00% Fee Deduction)
        elif tx_type == 'WITHDRAW':
            if profile.current_balance < gross_amount:
                return Response({
                    "error": f"Insufficient portfolio balance! Current balance: ${profile.current_balance:.2f}"
                }, status=status.HTTP_400_BAD_REQUEST)

            fee_percentage = decimal.Decimal(str(settings.WITHDRAWAL_FEE_PERCENT))  # 1.00%
            fee_amount = (gross_amount * fee_percentage) / decimal.Decimal('100.00')
            net_amount = gross_amount - fee_amount
            amount_bdt = gross_amount * decimal.Decimal(str(settings.USD_TO_BDT_RATE))

            # Deduct Gross Amount from User Balance
            profile.current_balance -= gross_amount
            profile.save()

            wallet_tx = WalletTransaction.objects.create(
                user=request.user,
                transaction_type='WITHDRAW',
                payment_method=payment_method,
                tran_id=tran_id,
                gross_amount=gross_amount,
                fee_percentage=fee_percentage,
                fee_amount=fee_amount,
                net_amount=net_amount,
                amount_bdt=amount_bdt,
                status='COMPLETED',
                account_number=account_number,
                reference_note=reference_note
            )

            return Response({
                "message": f"Withdrawal request of ${gross_amount:.2f} submitted. 1% Fee: ${fee_amount:.2f}. Net Payout: ${net_amount:.2f}",
                "new_balance": float(profile.current_balance),
                "transaction": WalletTransactionSerializer(wallet_tx).data
            }, status=status.HTTP_201_CREATED)

        else:
            return Response({"error": "Invalid transaction type."}, status=status.HTTP_400_BAD_REQUEST)


class SSLCommerzInitiateView(APIView):
    """
    SSLCommerz Sandbox Payment Gateway Initiation (Cash In via SSLCommerz Gateway)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        amount_str = request.data.get('amount', '0')
        account_number = request.data.get('account_number', '')

        try:
            gross_amount = decimal.Decimal(str(amount_str))
            if gross_amount <= 0:
                return Response({"error": "Amount must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, decimal.InvalidOperation):
            return Response({"error": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        fee_percentage = decimal.Decimal(str(settings.CASH_IN_FEE_PERCENT))  # 1.00%
        fee_amount = (gross_amount * fee_percentage) / decimal.Decimal('100.00')
        net_amount = gross_amount - fee_amount
        amount_bdt = gross_amount * decimal.Decimal(str(settings.USD_TO_BDT_RATE))
        tran_id = f"STKCAST_DEP_{int(time.time())}_{request.user.id}"

        # Create Pending Transaction in Database
        wallet_tx = WalletTransaction.objects.create(
            user=request.user,
            transaction_type='CASH_IN',
            payment_method='SSLCommerz',
            tran_id=tran_id,
            gross_amount=gross_amount,
            fee_percentage=fee_percentage,
            fee_amount=fee_amount,
            net_amount=net_amount,
            amount_bdt=amount_bdt,
            status='PENDING',
            account_number=account_number,
            reference_note='SSLCommerz Deposit'
        )

        host = request.build_absolute_uri('/')[:-1]
        success_url = f"{host}/api/portfolio/payment/sslcommerz/success/"
        fail_url = f"{host}/api/portfolio/payment/sslcommerz/fail/"
        cancel_url = f"{host}/api/portfolio/payment/sslcommerz/cancel/"

        res = initiate_sslcommerz_session(
            transaction=wallet_tx,
            user=request.user,
            success_url=success_url,
            fail_url=fail_url,
            cancel_url=cancel_url
        )

        if res.get('status') == 'SUCCESS':
            return Response({
                "status": "SUCCESS",
                "gateway_url": res['gateway_url'],
                "tran_id": tran_id,
                "amount": float(gross_amount),
                "amount_bdt": float(amount_bdt)
            }, status=status.HTTP_200_OK)
        else:
            wallet_tx.status = 'FAILED'
            wallet_tx.save()
            return Response({
                "status": "FAILED",
                "message": res.get('failed_reason', 'SSLCommerz gateway initiation failed.')
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzSuccessCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')

        try:
            wallet_tx = WalletTransaction.objects.get(tran_id=tran_id)
            if wallet_tx.status != 'COMPLETED':
                wallet_tx.status = 'COMPLETED'
                wallet_tx.val_id = val_id
                wallet_tx.save()

                # Atomically update balance
                profile, _ = UserProfile.objects.get_or_create(user=wallet_tx.user)
                profile.current_balance += wallet_tx.net_amount
                profile.save()

            return HttpResponse(
                "<h2>Payment Successful!</h2><p>Your deposit has been credited to your StockCast Wallet.</p>",
                content_type="text/html"
            )
        except WalletTransaction.DoesNotExist:
            return HttpResponse("<h2>Transaction Not Found</h2>", content_type="text/html", status=404)


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzFailCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        tran_id = request.data.get('tran_id')
        if tran_id:
            WalletTransaction.objects.filter(tran_id=tran_id).update(status='FAILED')
        return HttpResponse(
            "<h2>Payment Failed</h2><p>The transaction was declined or failed. Please try again.</p>",
            content_type="text/html"
        )


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzCancelCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        tran_id = request.data.get('tran_id')
        if tran_id:
            WalletTransaction.objects.filter(tran_id=tran_id).update(status='CANCELLED')
        return HttpResponse(
            "<h2>Payment Cancelled</h2><p>You cancelled the SSLCommerz payment process.</p>",
            content_type="text/html"
        )
