from django.urls import path
from . import view_loan
urlpatterns = [
    path('view-loan/<int:loan_id>/', view_loan, name='view_loan'),
]