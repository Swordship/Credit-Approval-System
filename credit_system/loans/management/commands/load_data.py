import pandas as pd
from django.core.management.base import BaseCommand
from loans.models import Customer, Loan
from django.db import transaction

class Command(BaseCommand):
    help = 'Load customer and loan data from Excel files'

    def handle(self, *args, **kwargs):

        print("Loading customers...")
        # Read customer_data.xlsx with pandas
        # customer_df = pd.read_excel('path/to/file')
        customer_df = pd.read_excel('C:\\Users\\project\\Documents\\Alemeno - Internship assigment\\Credit Approval System - Backend\\Business_Records\\customer_data.xlsx')
        
        # Create a mapping dictionary
        # customer_map = {}  # {excel_customer_id: django_customer_object}
        customer_map = {}
        
        # Loop through customers and create Customer objects
        # for index, row in customer_df.iterrows():
        #           customer = Customer.objects.create(...)
        #           customer_map[row['Customer ID']] = customer
        for index, row in customer_df.iterrows():
            customer = Customer.objects.create(
                first_name=row['First Name'],
                last_name=row['Last Name'],
                age=row['Age'],
                phone_number=row['Phone Number'],
                monthly_salary=row['Monthly Salary'],
                approved_limit=row['Approved Limit'],
                current_debt=row.get('Current Debt', 0)  # Default to 0 if not present
            )

            customer_map[row['Customer ID']] = customer

            print(f"✓ Created {len(customer_map)} customers")
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(customer_map)} customers'))
        
        # Read loan_data.xlsx with pandas
        loan_df = pd.read_excel('C:\\Users\\project\\Documents\\Alemeno - Internship assigment\\Credit Approval System - Backend\\Business_Records\\loan_data.xlsx')
        
        # Loop through loans and create Loan objects
        # Use customer_map to get the correct customer object!
        #       customer_obj = customer_map[row['Customer ID']]
        for index, row in loan_df.iterrows():
            customer_obj = customer_map[row['Customer ID']]
            Loan.objects.create(
                customer=customer_obj,
                loan_amount=row['Loan Amount'],
                tenure=row['Tenure'],
                interest_rate=row['Interest Rate'],
                monthly_payment=row['Monthly payment'],
                emis_paid_on_time=row['EMIs paid on Time'],
                date_of_approval=row['Date of Approval'].date(),
                end_date=row['End Date'].date()
            )
            print(f"✓ Created loan for customer {customer_obj}")
        print(f"✓ Created {len(loan_df)} loans")
        print("DONE!")
        
        self.stdout.write(self.style.SUCCESS('Data loaded successfully!'))