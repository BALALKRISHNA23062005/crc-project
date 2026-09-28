from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import Member

class SignUpForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15)

    def clean_email(self):
        email = self.cleaned_data['email']
        if Member.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not re.fullmatch(r'(?:\+91[ -]?)?[6-9]\d{9}', phone):
            raise ValidationError('Enter a valid 10-digit Indian mobile number.')
        return phone