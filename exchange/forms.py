from django import forms
from django.forms import ModelForm
from django.core.validators import MaxValueValidator, MinValueValidator
from .models import Trade
from .models import Recruiter
from .models import Portfolio
from django import forms

class BuyForm(forms.ModelForm):
    amount = forms.FloatField(min_value=0.0)
    class Meta:
        model = Trade
        fields = ['amount']

class SellForm(forms.ModelForm):
    amount = forms.FloatField(min_value=0.0)
    class Meta:
        model = Trade
        fields = ['amount']

class RecruiterForm(forms.ModelForm):
    class Meta:
        model = Recruiter
        fields = ['name', 'company', 'job_title', 'description', 'number', 'salary']