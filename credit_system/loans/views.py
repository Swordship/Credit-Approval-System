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

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from loans.models import Customer, Loan

def months_between(start_date, end_date):
    """Calculate number of months between two dates"""
    if end_date < start_date:
        return 0
    delta = relativedelta(end_date, start_date)
    return delta.years * 12 + delta.months

def calculate_credit_score(customer):
    """
    Calculate credit score (0-100) for a customer
    Current date: 2026-02-09
    """
    current_date = date(2026, 2, 9)
    
    # Get all customer loans
    loans = customer.loans.all()
    
    if len(loans) == 0:
        return 0  # No credit history
    
    # OVERRIDE: Check if current debt > approved limit
    # Calculate current debt
    # For each ACTIVE loan, calculate remaining amount
    # remaining = loan_amount - (emis_paid * monthly_payment)
    # Then sum all active loan remainings
    
    current_debt = Decimal(0)
    for loan in loans:
        # Check if loan is still active (end_date >= current_date)
        # If active, calculate remaining debt
        # Add to current_debt
        if loan.end_date >= current_date:
            remaining = loan.loan_amount - (loan.emis_paid_on_time * loan.monthly_payment)
            current_debt += remaining

        pass
    
    if current_debt > customer.approved_limit:
        return 0  # OVERRIDE CONDITION
    
    
    # ========== COMPONENT 1: PAYMENT HISTORY (50 points) ==========
    total_payment_score = 0
    
    for loan in loans:
        # Calculate payment ratio for this loan
        # 
        # If loan ended before today:
        #     payment_ratio = emis_paid / tenure
        # Else (loan still active):
        #     expected_emis = months_between(start_date, today)
        #     payment_ratio = min(emis_paid / expected_emis, 1.0)
        
        # Write the logic here
        if loan.end_date < current_date:
            payment_ratio = loan.emis_paid_on_time / loan.tenure
        else:
            expected_emis = months_between(loan.date_of_approval, current_date)
            if expected_emis > 0:
                payment_ratio = min(loan.emis_paid_on_time / expected_emis, 1.0)
            else:
                payment_ratio = 1.0  # If loan just started, consider it good payment history
        total_payment_score += payment_ratio

    payment_history_score = (total_payment_score / len(loans)) * 50
    
    
    # ========== COMPONENT 2: NUMBER OF LOANS (15 points) ==========
    num_loans = len(loans)
    
    # Assign score based on number of loans
    # 0 loans: 0 points
    # 1-3 loans: 15 points
    # 4-6 loans: 10 points
    # 7+ loans: 5 points
    
    if num_loans == 0:
        num_loans_score = 0
    elif 1 <= num_loans <= 3:
        num_loans_score = 15
    elif 4 <= num_loans <= 6:
        num_loans_score = 10
    else:
        num_loans_score = 5  # 7+ loans: 5 points
    
    
    # ========== COMPONENT 3: LOAN VOLUME (20 points) ==========
    # We already calculated current_debt above
    
    if customer.approved_limit > 0:
        utilization_ratio = float(current_debt / customer.approved_limit)
    else:
        utilization_ratio = 0
    
    # Score based on utilization
    # < 30%: 20 points
    # 30-50%: 15 points
    # 50-80%: 10 points
    # > 80%: 5 points
    
    if utilization_ratio < 0.3:
        volume_score = 20
    elif 0.3 <= utilization_ratio < 0.5:
        volume_score = 15
    elif 0.5 <= utilization_ratio < 0.8:
        volume_score = 10
    else:
        volume_score = 5  # > 80% utilization: 5 points
    
    
    # ========== COMPONENT 4: CURRENT YEAR ACTIVITY (15 points) ==========
    current_year = 2026
    active_loans_2026 = 0
    
    for loan in loans:
        # Check if loan is active in 2026
        # loan started <= 2026 AND loan ends >= 2026
        # Write the logic
        if loan.date_of_approval.year <= current_year and loan.end_date.year >= current_year:
            active_loans_2026 += 1
        # pass
    
    # Score based on active loans
    # 0 active: 15 points
    # 1-2 active: 10 points
    # 3+ active: 5 points
    
    if active_loans_2026 == 0:
        activity_score = 15
    elif 1 <= active_loans_2026 <= 2:
        activity_score = 10
    else:
        activity_score = 5
    
    
    # ========== TOTAL SCORE ==========
    total_score = payment_history_score + num_loans_score + volume_score + activity_score
    
    return round(total_score)