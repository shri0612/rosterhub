from django.contrib import admin
from .models import PayrollSummary


@admin.register(PayrollSummary)
class PayrollSummaryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee",
        "weekly_roster",
        "total_hours",
        "standard_hours",
        "overtime_hours",
        "gross_pay",
        "calculation_status",
        "calculated_at",
    )
    list_filter = ("calculation_status", "weekly_roster")
    search_fields = ("employee__name", "employee__email")
    ordering = ("-calculated_at",)