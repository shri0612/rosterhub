from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta

from apps.employees.models import Employee


class WeeklyRoster(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("finalized", "Finalized"),
    ]

    week_start_date = models.DateField(unique=True)  # Monday
    week_end_date = models.DateField()               # Sunday
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_start_date"]

    def __str__(self):
        return f"Roster: {self.week_start_date} to {self.week_end_date} ({self.status})"

    def clean(self):
        # Ensure week_end_date is 6 days after week_start_date (Mon-Sun window)
        if self.week_start_date and self.week_end_date:
            expected_end = self.week_start_date + timedelta(days=6)
            if self.week_end_date != expected_end:
                raise ValidationError("week_end_date must be exactly 6 days after week_start_date.")

    def save(self, *args, **kwargs):
        # Auto-fill week_end_date if not provided
        if self.week_start_date and not self.week_end_date:
            self.week_end_date = self.week_start_date + timedelta(days=6)
        self.full_clean()
        super().save(*args, **kwargs)


class Shift(models.Model):
    SHIFT_STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("off", "Off"),
        ("leave", "Leave"),
        ("holiday", "Holiday"),
    ]

    weekly_roster = models.ForeignKey(
        WeeklyRoster,
        on_delete=models.CASCADE,
        related_name="shifts"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="shifts"
    )

    shift_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    break_minutes = models.PositiveIntegerField(default=0)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    shift_status = models.CharField(max_length=20, choices=SHIFT_STATUS_CHOICES, default="assigned")
    notes = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["shift_date", "employee__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["weekly_roster", "employee", "shift_date"],
                name="unique_shift_per_employee_per_day_per_roster"
            )
        ]

    def __str__(self):
        return f"{self.employee.name} - {self.shift_date} ({self.shift_status})"

    def calculate_total_hours(self):
        """
        Calculates total hours = (end_time - start_time) - break_minutes
        Returns Decimal with 2 decimal places.
        """
        if self.shift_status != "assigned":
            return Decimal("0.00")

        if not self.start_time or not self.end_time:
            return Decimal("0.00")

        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)

        if end_dt <= start_dt:
            raise ValidationError("End time must be after start time.")

        duration_minutes = int((end_dt - start_dt).total_seconds() // 60)
        net_minutes = duration_minutes - self.break_minutes

        if net_minutes < 0:
            raise ValidationError("Break minutes cannot exceed total shift duration.")

        hours = Decimal(net_minutes) / Decimal(60)
        return hours.quantize(Decimal("0.01"))

    def clean(self):
        # Ensure shift_date belongs to the weekly roster range
        if self.weekly_roster and self.shift_date:
            if not (self.weekly_roster.week_start_date <= self.shift_date <= self.weekly_roster.week_end_date):
                raise ValidationError("shift_date must be within the weekly roster date range.")

        # Validation for assigned shifts
        if self.shift_status == "assigned":
            if not self.start_time or not self.end_time:
                raise ValidationError("Assigned shifts require start_time and end_time.")
        else:
            # For off/leave/holiday, times should be empty
            if self.start_time or self.end_time:
                raise ValidationError("Off/Leave/Holiday shifts should not have start_time or end_time.")

        # Validate and calculate total hours
        self.total_hours = self.calculate_total_hours()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)