from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Watchlist, Transaction, UserProfile, WalletTransaction
from market_data.serializers import StockSerializer

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        
        email = attrs['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        username = attrs.get('username')
        if not username or username.strip() == '':
            # Generate unique username from email
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            attrs['username'] = username
        else:
            if User.objects.filter(username__iexact=username).exists():
                raise serializers.ValidationError({"username": "A user with this username already exists."})
                
        attrs['email'] = email
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        name = validated_data.get('name', '')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=name
        )
        # Create user profile with starting demo balance
        UserProfile.objects.get_or_create(user=user, defaults={'current_balance': 50000.00})
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['current_balance']

class WatchlistSerializer(serializers.ModelSerializer):
    stock_details = StockSerializer(source='stock', read_only=True)

    class Meta:
        model = Watchlist
        fields = ['id', 'stock', 'stock_details', 'added_at']

class TransactionSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2, source='total_amount', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'stock', 'stock_symbol', 'transaction_type', 'quantity', 'price_per_share', 'total_value', 'timestamp']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'payment_method', 'tran_id', 'val_id',
            'gross_amount', 'fee_percentage', 'fee_amount', 'net_amount', 'amount_bdt',
            'status', 'account_number', 'reference_note', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tran_id', 'val_id', 'fee_percentage', 'fee_amount',
            'net_amount', 'amount_bdt', 'status', 'created_at', 'updated_at'
        ]
