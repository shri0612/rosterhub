from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "name",
            "email",
            "hourly_rate",
            "age",
            "department",
            "employment_type",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Enter full name"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "Enter email"}),
            "hourly_rate": forms.NumberInput(attrs={"class": "form-input", "step": "0.01", "placeholder": "e.g. 20.50"}),
            "age": forms.NumberInput(attrs={"class": "form-input", "placeholder": "e.g. 28"}),
            "department": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Operations"}),
            "employment_type": forms.Select(attrs={"class": "form-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }