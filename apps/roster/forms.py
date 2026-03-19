from django import forms
from datetime import timedelta

from .models import WeeklyRoster


class WeeklyRosterSelectForm(forms.Form):
    week_start_date = forms.DateField(
        label="Week Start Date (Monday)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-input"})
    )

    def clean_week_start_date(self):
        date_value = self.cleaned_data["week_start_date"]
        # Monday = 0, Sunday = 6
        if date_value.weekday() != 0:
            raise forms.ValidationError("Please select a Monday date.")
        return date_value


class WeeklyRosterForm(forms.ModelForm):
    class Meta:
        model = WeeklyRoster
        fields = ["week_start_date", "week_end_date", "status"]
        widgets = {
            "week_start_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "week_end_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "status": forms.Select(attrs={"class": "form-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("week_start_date")
        end = cleaned_data.get("week_end_date")

        if start and end:
            expected_end = start + timedelta(days=6)
            if end != expected_end:
                raise forms.ValidationError("Week end date must be exactly 6 days after week start date.")
        return cleaned_data