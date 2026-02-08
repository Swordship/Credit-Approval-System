from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from .serializers import CustomerRegisterSerializer, CustomerResponseSerializer, LoanListSerializer, LoanSerializer
# Create your views here.

@api_view(['GET'])
def view_loan(request, loan_id):
    """
    API endpoint: /view-loan/<loan_id>
    Method: GET
    Returns: Loan details with customer info 
    """
    try : 
        loan = Loan.objects.get(id=loan_id)

    except Loan.DoesNotExist:
        return Response(
            {"error": "Loan not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = LoanSerializer(loan)

    return Response(serializer.data, status=status.HTTP_200_OK)
@api_view(['GET'])
def view_loans(request, customer_id):
    """
    API endpoint: /view-loan/<customer_id>
    Method: GET
    Returns: List of all loans for a customer 
    """
    try :
        customer = Customer.objects.get(id=customer_id)

    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    loans = customer.loans.all()  # Using related_name from ForeignKey
    serializer = LoanListSerializer(loans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
def round_to_nearest_lakh(amount):
    """Round amount to nearest lakh"""
    return round(amount / 100000) * 100000
@api_view(['POST'])
def register_customer(request):
    """
    API endpoint: /register
    Method: POST
    Input: first_name, last_name, age, monthly_income, phone_number
    Output: Created customer with approved_limit
    """
    serializer = CustomerRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    validated_data = serializer.validated_data
    # Calculate approved_limit BEFORE creating
    monthly_income = validated_data['monthly_income']
    approved_limit = round_to_nearest_lakh(36 * monthly_income)

    # Create customer with ALL fields at once
    customer = Customer.objects.create(
        first_name=validated_data['first_name'],
        last_name=validated_data['last_name'],
        age=validated_data['age'],
        monthly_salary=monthly_income,
        phone_number=validated_data['phone_number'],
        approved_limit=approved_limit,
        current_debt=0
    )

    # Return response with created customer data
    response_serializer = CustomerResponseSerializer(customer)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
