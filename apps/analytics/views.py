from decimal import Decimal
from datetime import timedelta

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Sum

from apps.roster.models import WeeklyRoster, Shift
from apps.employees.models import Employee
from .models import WorkforceAnalyticsResult
from utils.analytics_client import submit_and_wait_for_analysis

    
from django.shortcuts import render



def run_analytics_for_roster(request, roster_id):
    roster = get_object_or_404(WeeklyRoster, pk=roster_id)
    employees = Employee.objects.filter(is_active=True).order_by("name")

    success_count = 0
    fail_count = 0

    for emp in employees:
        # Build daily hours array Monday-Sunday
        daily_hours = []
        current_day = roster.week_start_date

        for _ in range(7):
            total_for_day = Shift.objects.filter(
                weekly_roster=roster,
                employee=emp,
                shift_date=current_day
            ).aggregate(total=Sum("total_hours"))["total"] or Decimal("0.00")

            # Friend API sample uses integers, so send rounded int for now
            daily_hours.append(float(total_for_day))
            current_day += timedelta(days=1)

        weekly_total = sum(daily_hours)

        payload = {
            "employee_id": f"EMP-{emp.id:03d}",
            "week_start": str(roster.week_start_date),
            "daily_hours": daily_hours,
            "hourly_rate": float(emp.hourly_rate),
        }

        api_result = submit_and_wait_for_analysis(payload, max_retries=6, delay_seconds=2)

        if api_result.get("success"):
            result = api_result.get("result") or {}

            WorkforceAnalyticsResult.objects.update_or_create(
                weekly_roster=roster,
                employee=emp,
                defaults={
                    "total_hours": Decimal(str(result.get("total_hours", weekly_total))),
                    "overtime_hours": Decimal(str(result.get("overtime_hours", 0))),
                    "risk_level": result.get("risk_level"),
                    "compliance_status": result.get("compliance_status"),
                    "estimated_pay": Decimal(str(result.get("estimated_pay", 0))),
                    "public_holidays_in_week": int(result.get("public_holidays_in_week", 0) or 0),
                    "recommendation": result.get("recommendation", ""),
                    "api_status": "success",
                    "job_id": api_result.get("job_id"),
                    "error_message": "",
                }
            )
            success_count += 1
        else:
            WorkforceAnalyticsResult.objects.update_or_create(
                weekly_roster=roster,
                employee=emp,
                defaults={
                    "total_hours": Decimal(str(weekly_total)),
                    "api_status": "failed",
                    "job_id": api_result.get("job_id"),
                    "error_message": api_result.get("error", "Unknown analytics API error"),
                }
            )
            fail_count += 1

    if fail_count == 0:
        messages.success(request, f"Analytics completed successfully for {success_count} employee(s).")
    else:
        messages.warning(request, f"Analytics completed with issues. Success: {success_count}, Failed: {fail_count}.")

    return redirect("roster:week_summary")
    



def analytics_summary(request):
    # roster = WeeklyRoster.objects.order_by("-week_start_date").first()
    active_roster_id = request.session.get("active_roster_id")
    if active_roster_id:
        roster = WeeklyRoster.objects.filter(id=active_roster_id).first()
    else:
        roster = WeeklyRoster.objects.order_by("-week_start_date").first()

    if not roster:
        return render(request, "analytics/summary.html", {"roster": None})

    analytics_rows = WorkforceAnalyticsResult.objects.filter(
        weekly_roster=roster
    ).select_related("employee").order_by("employee__name")

    context = {
        "roster": roster,
        "analytics_rows": analytics_rows,
    }
    return render(request, "analytics/summary.html", context)