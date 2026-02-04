from django.db import models

class Customer(models.Model):
    # Django auto-creates 'id' as primary key - you don't need to define it!
    
    # Write all 7 fields here:
    # 1. first_name
    # 2. last_name
    # 3. age
    # 4. phone_number
    # 5. monthly_salary (use your DecimalField specs!)
    # 6. approved_limit
    # 7. current_debt (with default=0)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=15)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=12, decimal_places=2)
    current_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Loan(models.Model):
    # Django auto-creates 'id' as primary key
    
    # Write all 8 fields here:
    # 1. customer (ForeignKey to Customer - IMPORTANT!)
    # 2. loan_amount
    # 3. tenure
    # 4. interest_rate
    # 5. monthly_payment
    # 6. emis_paid_on_time
    # 7. date_of_approval
    # 8. end_date
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    emis_paid_on_time = models.IntegerField()
    date_of_approval = models.DateField()
    end_date = models.DateField()
    
    def __str__(self):
        return f"Loan #{self.id} - Customer {self.customer.id}"