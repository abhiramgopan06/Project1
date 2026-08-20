from django.db import models

class Payment(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField()
    amount = models.DecimalField(decimal_places=2,max_digits=10)
    description = models.TextField(blank=True,null=True)
    razorpay_payment_link = models.URLField(blank=True,null=True)
    payment_id = models.CharField(max_length=100,blank=True,null=True)
    status = models.CharField(max_length=20,default='Pending')
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User name - {self.user_name}, Amount - {self.amount}"

    