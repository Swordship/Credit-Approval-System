from rest_framework import serializers
from .models import Customer, Loan

class CustomerSerializer(serializers.ModelSerializer):
    """
    This converts Customer objects to JSON
    """
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'age']
        # We only show these fields in the API response
class LoanSerializer(serializers.ModelSerializer):
    """
    This converts Loan objects to JSON
    """
    # Nested serializer - show customer details inside loan
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'id',
            'customer',
            'loan_amount',
            'interest_rate',
            'monthly_payment',
            'tenure'
        ]
class LoanListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing multiple loans
    Includes calculated field: repayments_left
    """
    # Nested serializer - show customer details inside loan
    customer = CustomerSerializer(read_only=True)
    repayments_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Loan
        fields = [
            'id',
            'customer',
            'loan_amount',
            'interest_rate',
            'monthly_payment',
            'tenure',
            'repayments_left'
        ]

    def get_repayments_left (self , obj):
        """
        Calculate repayments left
        obj = the Loan object
        """
        total_payments = obj.tenure
        payments_made = obj.emis_paid_on_time
        repayments_left = total_payments - payments_made
        return repayments_left
class CustomerRegisterSerializer(serializers.Serializer):
    """
    Serializer for /register endpoint
    Validates incoming data
    """
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2)
    phone_number = serializers.CharField(max_length=15)
class CustomerResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for /register response
    Returns the created customer data
    """
    class Meta:
        model = Customer
        fields = [
            'id',
            'first_name',
            'last_name',
            'age',
            'phone_number',
            'monthly_salary',
            'approved_limit'
        ]
class LoanEligibilityRequestSerializer(serializers.Serializer):
    """
    Serializer for /check-eligibility request
    """
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()
class LoanCreateResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for /create-loan response
    """
    class Meta:
        model = Loan
        fields = [
            'id',
            'customer',
            'loan_amount',
            'interest_rate',
            'monthly_payment',
            'tenure'
        ]