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