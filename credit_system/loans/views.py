from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Loan
from .serializers import LoanSerializer
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

    except loan.DoesNotExist:
        return Response(
            {"error": "Loan not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = LoanSerializer(loan)

    return Response(serializer.data, status=status.HTTP_200_OK)

pass