from django import forms
from .models import Registration
from members.models import Member

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['member', 'event']