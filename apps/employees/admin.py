from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "email",
        "hourly_rate",
        "age",
        "employment_type",
        "is_active",
        "created_at",
    )
    list_filter = ("employment_type", "is_active", "created_at")
    search_fields = ("name", "email", "department")
    ordering = ("name",)