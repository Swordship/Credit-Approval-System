from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from .serializers import CustomerRegisterSerializer, CustomerResponseSerializer, LoanEligibilityRequestSerializer, LoanListSerializer, LoanSerializer
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from .utils import get_current_date
# from loans.models import Customer, Loan
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
    current_date = get_current_date()
    
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

        # pass
    
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
def calculate_emi(loan_amount, annual_interest_rate, tenure_months):
    """
    Calculate monthly EMI using compound interest formula
    EMI = [P × r × (1+r)^n] / [(1+r)^n - 1]
    where:
    P = loan amount
    r = monthly interest rate (annual rate / 12 / 100)
    n = tenure in months
    """
    # YOUR TASK: Implement the EMI formula
    # Hint 1: Convert annual interest rate to monthly: monthly_rate = annual_rate / 12 / 100
    # Hint 2: Use the formula above
    # Hint 3: Handle edge case: if interest_rate = 0, EMI = loan_amount / tenure
    if annual_interest_rate == 0:
        return loan_amount / tenure_months
    monthly_rate = annual_interest_rate / 12 / 100
    emi = (loan_amount * monthly_rate * (1 + monthly_rate) ** tenure_months) / ((1 + monthly_rate) ** tenure_months - 1)
    return emi
    
    # pass  # Remove and write your code

@api_view(['POST'])
def check_eligibility(request):
    """
    API endpoint: /check-eligibility
    Method: POST
    Input: customer_id, loan_amount, interest_rate, tenure
    Output: approval decision with corrected interest rate and EMI
    """
    
    # Step 1: Validate input
    serializer = LoanEligibilityRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    customer_id = validated_data['customer_id']
    loan_amount = validated_data['loan_amount']
    interest_rate = validated_data['interest_rate']
    tenure = validated_data['tenure']
    
    # Step 2: Get customer
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Step 3: Calculate credit score
    credit_score = calculate_credit_score(customer)
    
    # Step 4: Check EMI constraint (sum of current EMIs > 50% salary?)
    # YOUR TASK: Calculate sum of monthly payments for all active loans
    # Hint: Loop through customer.loans.all(), check if active, sum monthly_payment
    
    current_emis = Decimal(0)
    # TODO: Write the logic here
    for loan in customer.loans.all():
        if loan.end_date >= get_current_date():  # Check if loan is active
            current_emis += loan.monthly_payment
    
    # Check if adding new EMI would exceed 50% of salary
    new_emi = calculate_emi(loan_amount, interest_rate, tenure)
    total_emis_with_new_loan = current_emis + Decimal(new_emi)
    
    if total_emis_with_new_loan > (customer.monthly_salary * Decimal(0.5)):
        return Response({
            "customer_id": customer_id,
            "approval": False,
            "interest_rate": float(interest_rate),
            "corrected_interest_rate": float(interest_rate),
            "tenure": tenure,
            "monthly_installment": float(new_emi),
            "message": "Sum of current EMIs exceeds 50% of monthly salary"
        })
    
    # Step 5: Determine approval and correct interest rate based on credit score
    # YOUR TASK: Implement the approval logic
    #
    # If credit_score > 50:
    #     approval = True
    #     corrected_rate = interest_rate (no change)
    #
    # If 30 < credit_score <= 50:
    #     if interest_rate < 12:
    #         corrected_rate = 12
    #     else:
    #         corrected_rate = interest_rate
    #     approval = True
    #
    # If 10 < credit_score <= 30:
    #     if interest_rate < 16:
    #         corrected_rate = 16
    #     else:
    #         corrected_rate = interest_rate
    #     approval = True
    #
    # If credit_score <= 10:
    #     approval = False
    
    # TODO: Write the logic here
    if credit_score > 50:
        approval = True
        corrected_interest_rate = interest_rate
    elif 30 < credit_score <= 50:
        approval = True
        if interest_rate < 12:
            corrected_interest_rate = Decimal(12)
        else:
            corrected_interest_rate = interest_rate
    elif 10 < credit_score <= 30:
        approval = True
        if interest_rate < 16:
            corrected_interest_rate = Decimal(16)
        else:
            corrected_interest_rate = interest_rate
    else:  # credit_score <= 10
        approval = False
        corrected_interest_rate = interest_rate

    # approval = False
    # corrected_interest_rate = interest_rate
    
    # Recalculate EMI with corrected interest rate
    final_emi = calculate_emi(loan_amount, corrected_interest_rate, tenure)
    
    # Return response
    return Response({
        "customer_id": customer_id,
        "approval": approval,
        "interest_rate": float(interest_rate),
        "corrected_interest_rate": float(corrected_interest_rate),
        "tenure": tenure,
        "monthly_installment": float(final_emi)
    })
@api_view(['POST'])
def create_loan(request):
    """
    API endpoint: /create-loan
    Method: POST
    Input: customer_id, loan_amount, interest_rate, tenure
    Output: Created loan if approved, error message if rejected
    """
    
    # Step 1: Validate input
    serializer = LoanEligibilityRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    customer_id = validated_data['customer_id']
    loan_amount = validated_data['loan_amount']
    interest_rate = validated_data['interest_rate']
    tenure = validated_data['tenure']
    
    # Step 2: Get customer
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response(
            {"error": "Customer not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Step 3: Calculate credit score
    credit_score = calculate_credit_score(customer)
    
    # Step 4: Check EMI constraint
    current_emis = Decimal(0)
    current_date = get_current_date()
    
    for loan in customer.loans.all():
        if loan.end_date >= current_date:
            current_emis += loan.monthly_payment
    
    new_emi = calculate_emi(loan_amount, interest_rate, tenure)
    total_emis_with_new_loan = current_emis + Decimal(new_emi)
    
    if total_emis_with_new_loan > (customer.monthly_salary * Decimal(0.5)):
        return Response({
            "loan_id": None,
            "customer_id": customer_id,
            "loan_approved": False,
            "message": "Sum of current EMIs exceeds 50% of monthly salary",
            "monthly_installment": float(new_emi)
        })
    
    # Step 5: Determine approval and corrected interest rate
    if credit_score > 50:
        approval = True
        corrected_interest_rate = interest_rate
    elif 30 < credit_score <= 50:
        approval = True
        if interest_rate < 12:
            corrected_interest_rate = Decimal(12)
        else:
            corrected_interest_rate = interest_rate
    elif 10 < credit_score <= 30:
        approval = True
        if interest_rate < 16:
            corrected_interest_rate = Decimal(16)
        else:
            corrected_interest_rate = interest_rate
    else:  # credit_score <= 10
        approval = False
        corrected_interest_rate = interest_rate
    
    # Step 6: If NOT approved, return rejection
    if not approval:
        return Response({
            "loan_id": None,
            "customer_id": customer_id,
            "loan_approved": False,
            "message": f"Credit score too low (score: {credit_score})",
            "monthly_installment": float(new_emi)
        })
    
    # Step 7: If APPROVED, create the loan!
    final_emi = calculate_emi(loan_amount, corrected_interest_rate, tenure)
    
    # Calculate dates
    start_date = get_current_date()
    end_date = start_date + relativedelta(months=tenure)
    
    # Create loan object
    new_loan = Loan.objects.create(
        customer=customer,
        loan_amount=loan_amount,
        tenure=tenure,
        interest_rate=corrected_interest_rate,
        monthly_payment=final_emi,
        emis_paid_on_time=0,
        date_of_approval=start_date,
        end_date=end_date
    )
    
    # Step 8: Return success response
    return Response({
        "loan_id": new_loan.id,
        "customer_id": customer_id,
        "loan_approved": True,
        "message": "Loan approved",
        "monthly_installment": float(final_emi)
    }, status=status.HTTP_201_CREATED)
# ============================================================================
# DEBUG ENDPOINTS (Remove these in production!)
# ============================================================================

@api_view(['GET'])
def system_info(request):
    """
    API endpoint: /system-info
    Method: GET
    Returns: System configuration info
    Shows what date the system is currently using
    """
    from django.conf import settings
    
    reference_date = getattr(settings, 'SYSTEM_REFERENCE_DATE', None)
    current_date = get_current_date()
    
    return Response({
        "system_mode": "DEMO" if reference_date else "PRODUCTION",
        "reference_date_setting": reference_date,
        "current_system_date": str(current_date),
        "actual_today": str(date.today()),
        "message": "DEMO mode uses reference date. PRODUCTION mode uses real current date."
    })


@api_view(['GET'])
def debug_credit_score(request, customer_id):
    """
    API endpoint: /debug-score/<customer_id>
    Method: GET
    Returns: Detailed credit score breakdown
    """
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    
    # Calculate credit score
    score = calculate_credit_score(customer)
    
    # Get loan statistics
    current_date = get_current_date()
    total_loans = customer.loans.count()
    active_loans = customer.loans.filter(end_date__gte=current_date).count()
    completed_loans = customer.loans.filter(end_date__lt=current_date).count()
    
    # Calculate current debt
    current_debt = Decimal(0)
    for loan in customer.loans.all():
        if loan.end_date >= current_date:
            remaining = loan.loan_amount - (Decimal(loan.emis_paid_on_time) * loan.monthly_payment)
            current_debt += remaining
    
    return Response({
        "customer_id": customer_id,
        "customer_name": f"{customer.first_name} {customer.last_name}",
        "credit_score": score,
        "approved_limit": float(customer.approved_limit),
        "current_debt": float(current_debt),
        "debt_utilization": f"{float((current_debt / customer.approved_limit) * 100):.2f}%" if customer.approved_limit > 0 else "0%",
        "loan_statistics": {
            "total_loans": total_loans,
            "active_loans": active_loans,
            "completed_loans": completed_loans
        },
        "approval_guidance": {
            "50-100": "Loan approved at requested rate",
            "30-50": "Loan approved, minimum 12% interest",
            "10-30": "Loan approved, minimum 16% interest",
            "0-10": "Loan rejected - too risky"
        }
    })


@api_view(['GET'])
def debug_customer_emis(request, customer_id):
    """
    API endpoint: /debug-emis/<customer_id>
    Method: GET
    Returns: Detailed EMI breakdown and loan capacity
    """
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    
    current_date = get_current_date()
    active_loans = []
    total_emis = Decimal(0)
    
    for loan in customer.loans.all():
        if loan.end_date >= current_date:
            active_loans.append({
                "loan_id": loan.id,
                "loan_amount": float(loan.loan_amount),
                "monthly_payment": float(loan.monthly_payment),
                "emis_paid": loan.emis_paid_on_time,
                "total_emis": loan.tenure,
                "repayments_left": loan.tenure - loan.emis_paid_on_time,
                "date_of_approval": str(loan.date_of_approval),
                "end_date": str(loan.end_date)
            })
            total_emis += loan.monthly_payment
    
    fifty_percent = customer.monthly_salary * Decimal(0.5)
    remaining_capacity = fifty_percent - total_emis
    
    return Response({
        "customer_id": customer_id,
        "customer_name": f"{customer.first_name} {customer.last_name}",
        "monthly_salary": float(customer.monthly_salary),
        "fifty_percent_salary": float(fifty_percent),
        "current_total_emis": float(total_emis),
        "emi_utilization_percentage": f"{float((total_emis / customer.monthly_salary) * 100):.2f}%",
        "remaining_emi_capacity": float(remaining_capacity),
        "can_afford_new_loan": remaining_capacity > 0,
        "max_new_emi_allowed": float(max(remaining_capacity, 0)),
        "active_loans_count": len(active_loans),
        "active_loans": active_loans,
        "status": "OVER LIMIT" if total_emis > fifty_percent else "WITHIN LIMIT"
    })