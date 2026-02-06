from django.urls import path
from . import views
urlpatterns = [
    path('view-loan/<int:loan_id>/', views.view_loan, name='view_loan'),
]