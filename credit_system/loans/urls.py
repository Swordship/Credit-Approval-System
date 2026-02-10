from django.urls import path
from . import views
urlpatterns = [
    path('view-loan/<int:loan_id>/', views.view_loan, name='view_loan'),
    path('view-loans/<int:customer_id>/', views.view_loans, name='view_loans'),
    path('register/', views.register_customer, name='register'),
    path ('check-eligibility/', views.check_eligibility, name='check_eligibility'),
    path('create-loan/', views.create_loan, name='create_loan'),

     # Debug endpoints (remove in production)
    path('system-info/', views.system_info, name='system_info'),
    path('debug-score/<int:customer_id>/', views.debug_credit_score, name='debug_score'),
    path('debug-emis/<int:customer_id>/', views.debug_customer_emis, name='debug_emis'),
]