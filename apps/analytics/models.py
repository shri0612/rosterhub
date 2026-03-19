from django.db import models

from apps.employees.models import Employee
from apps.roster.models import WeeklyRoster


class WorkforceAnalyticsResult(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    weekly_roster = models.ForeignKey(
        WeeklyRoster,
        on_delete=models.CASCADE,
        related_name="analytics_results"
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="analytics_results"
    )

    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    risk_level = models.CharField(max_length=20, blank=True, null=True)
    compliance_status = models.CharField(max_length=20, blank=True, null=True)

    estimated_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    public_holidays_in_week = models.PositiveIntegerField(default=0)
    recommendation = models.TextField(blank=True, null=True)

    api_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    job_id = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    analyzed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["weekly_roster", "employee"],
                name="unique_analytics_per_employee_per_week"
            )
        ]

    def __str__(self):
        return f"Analytics - {self.employee.name} ({self.weekly_roster.week_start_date})"