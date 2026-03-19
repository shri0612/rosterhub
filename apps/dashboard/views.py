from django.shortcuts import render
from django.db.models import Sum

from apps.employees.models import Employee
from apps.roster.models import WeeklyRoster, Shift


def home(request):
    total_employees = Employee.objects.count()

    latest_roster = WeeklyRoster.objects.order_by("-week_start_date").first()

    if latest_roster:
        employees_scheduled = Shift.objects.filter(
            weekly_roster=latest_roster,
            shift_status="assigned"
        ).values("employee_id").distinct().count()

        total_weekly_hours = Shift.objects.filter(
            weekly_roster=latest_roster
        ).aggregate(total=Sum("total_hours"))["total"] or 0
    else:
        employees_scheduled = 0
        total_weekly_hours = 0

    total_payroll = 0  # will be connected after payroll module

    context = {
        "total_employees": total_employees,
        "employees_scheduled": employees_scheduled,
        "total_weekly_hours": total_weekly_hours,
        "total_payroll": total_payroll,
    }
    return render(request, "dashboard/home.html", context)