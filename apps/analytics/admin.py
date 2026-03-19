from django.contrib import admin
from .models import WorkforceAnalyticsResult


@admin.register(WorkforceAnalyticsResult)
class WorkforceAnalyticsResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee",
        "weekly_roster",
        "total_hours",
        "overtime_hours",
        "risk_level",
        "compliance_status",
        "estimated_pay",
        "api_status",
        "analyzed_at",
    )
    list_filter = ("api_status", "risk_level", "compliance_status", "weekly_roster")
    search_fields = ("employee__name", "employee__email", "job_id")
    ordering = ("-analyzed_at",)