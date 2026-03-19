from django.contrib import admin
from .models import WeeklyRoster, Shift


@admin.register(WeeklyRoster)
class WeeklyRosterAdmin(admin.ModelAdmin):
    list_display = ("id", "week_start_date", "week_end_date", "status", "created_at")
    list_filter = ("status", "week_start_date")
    search_fields = ("week_start_date",)
    ordering = ("-week_start_date",)


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "employee",
        "weekly_roster",
        "shift_date",
        "shift_status",
        "start_time",
        "end_time",
        "break_minutes",
        "total_hours",
    )
    list_filter = ("shift_status", "shift_date", "weekly_roster")
    search_fields = ("employee__name", "employee__email")
    ordering = ("shift_date", "employee__name")