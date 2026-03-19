from decimal import Decimal

from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Sum

from apps.roster.models import WeeklyRoster, Shift
from apps.employees.models import Employee
from .models import PayrollSummary
from utils.payroll_client import call_payroll_api
from django.shortcuts import render


def calculate_payroll_for_roster(request, roster_id):
    roster = get_object_or_404(WeeklyRoster, pk=roster_id)

    employees = Employee.objects.filter(is_active=True).order_by("name")

    success_count = 0
    fail_count = 0

    for emp in employees:
        # Sum total hours for this employee in this roster
        total_hours = Shift.objects.filter(
            weekly_roster=roster,
            employee=emp
        ).aggregate(total=Sum("total_hours"))["total"] or Decimal("0.00")

        payload = {
            "employee_id": emp.id,
            "employee_name": emp.name,
            "hourly_rate": float(emp.hourly_rate),
            "total_hours": float(total_hours),
            "standard_hours_limit": 40,
            "overtime_multiplier": 1.5,
        }

        api_result = call_payroll_api(payload)

        if api_result["success"]:
            data = api_result["data"]

            PayrollSummary.objects.update_or_create(
                weekly_roster=roster,
                employee=emp,
                defaults={
                    "total_hours": Decimal(str(data.get("total_hours", 0))),
                    "standard_hours": Decimal(str(data.get("standard_hours", 0))),
                    "overtime_hours": Decimal(str(data.get("overtime_hours", 0))),
                    "hourly_rate": Decimal(str(data.get("hourly_rate", 0))),
                    "overtime_rate": Decimal(str(data.get("overtime_rate", 0))),
                    "standard_pay": Decimal(str(data.get("standard_pay", 0))),
                    "overtime_pay": Decimal(str(data.get("overtime_pay", 0))),
                    "gross_pay": Decimal(str(data.get("gross_pay", 0))),
                    "calculation_status": "success",
                    "error_message": "",
                }
            )
            success_count += 1
        else:
            PayrollSummary.objects.update_or_create(
                weekly_roster=roster,
                employee=emp,
                defaults={
                    "total_hours": total_hours,
                    "hourly_rate": emp.hourly_rate,
                    "calculation_status": "failed",
                    "error_message": api_result.get("error", "Unknown payroll API error"),
                }
            )
            fail_count += 1

    if fail_count == 0:
        messages.success(request, f"Payroll calculated successfully for {success_count} employee(s).")
    else:
        messages.warning(
            request,
            f"Payroll completed with issues. Success: {success_count}, Failed: {fail_count}."
        )

    # return redirect("roster:week_summary")
    
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")
    if next_url:
       return redirect(next_url)

    return redirect("payroll:summary")
    



def payroll_summary(request):
    # roster = WeeklyRoster.objects.order_by("-week_start_date").first()
    active_roster_id = request.session.get("active_roster_id")
    if active_roster_id:
      roster = WeeklyRoster.objects.filter(id=active_roster_id).first()
    else:
      roster = WeeklyRoster.objects.order_by("-week_start_date").first()

    if not roster:
        return render(request, "payroll/summary.html", {"roster": None})

    payroll_rows = PayrollSummary.objects.filter(
        weekly_roster=roster
    ).select_related("employee").order_by("employee__name")

    totals = payroll_rows.aggregate(
        total_hours=Sum("total_hours"),
        total_standard_pay=Sum("standard_pay"),
        total_overtime_pay=Sum("overtime_pay"),
        total_gross_pay=Sum("gross_pay"),
    )

    context = {
        "roster": roster,
        "payroll_rows": payroll_rows,
        "totals": totals,
    }
    return render(request, "payroll/summary.html", context)