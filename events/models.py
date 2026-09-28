from django.db import models
from members.models import Member


class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=200)
    max_participants = models.IntegerField()
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.title


import uuid

class Registration(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registered_on = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('paid', 'Paid')],
        default='pending'
    )
    qr_code = models.CharField(max_length=36, unique=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.name} - {self.event.title}"

class Attendance(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    checked_in_at = models.DateTimeField(auto_now_add=True)
    
class Payment(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)
    paid_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.registration}"