from django.db import models

from apps.employees.models import Employee
from apps.roster.models import WeeklyRoster


class PayrollSummary(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    weekly_roster = models.ForeignKey(
        WeeklyRoster,
        on_delete=models.CASCADE,
        related_name="payroll_summaries"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payroll_summaries"
    )

    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    standard_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    standard_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    calculation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, null=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["weekly_roster", "employee"],
                name="unique_payroll_per_employee_per_week"
            )
        ]

    def __str__(self):
        return f"Payroll - {self.employee.name} ({self.weekly_roster.week_start_date})"