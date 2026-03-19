from datetime import timedelta, datetime
from apps.payroll.models import PayrollSummary
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from apps.analytics.models import WorkforceAnalyticsResult
from apps.employees.models import Employee
from .models import WeeklyRoster, Shift
from .forms import WeeklyRosterSelectForm
from utils.email_service import send_shift_email




def _build_employee_shift_email_content(roster, employee):
    shifts = Shift.objects.filter(
        weekly_roster=roster,
        employee=employee
    ).order_by("shift_date")

    if not shifts.exists():
        return None

    lines = []
    total_hours = 0.0

    for shift in shifts:
        day_label = shift.shift_date.strftime("%a %Y-%m-%d")

        if shift.shift_status == "assigned" and shift.start_time and shift.end_time:
            line = (
                f"{day_label}: {shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')} "
                f"(Break: {shift.break_minutes} min, Hours: {shift.total_hours})"
            )
        else:
            line = f"{day_label}: {shift.get_shift_status_display()} (Hours: {shift.total_hours})"

        lines.append(line)
        total_hours += float(shift.total_hours or 0)

    subject = f"Your Shift Schedule: {roster.week_start_date} to {roster.week_end_date}"

    text_body = (
        f"Hello {employee.name},\n\n"
        f"Here is your shift schedule for the week {roster.week_start_date} to {roster.week_end_date}.\n\n"
        + "\n".join(lines)
        + f"\n\nTotal Weekly Hours: {round(total_hours, 2)}"
        + "\n\nIf you have any questions, please contact your manager."
        + "\n\nRegards,\nRosterHub"
    )

    html_body = f"""
    <html>
      <body>
        <p>Hello <strong>{employee.name}</strong>,</p>
        <p>Here is your shift schedule for the week <strong>{roster.week_start_date}</strong> to <strong>{roster.week_end_date}</strong>.</p>
        <ul>
          {''.join([f'<li>{line}</li>' for line in lines])}
        </ul>
        <p><strong>Total Weekly Hours:</strong> {round(total_hours, 2)}</p>
        <p>If you have any questions, please contact your manager.</p>
        <p>Regards,<br>RosterHub</p>
      </body>
    </html>
    """

    return {
        "subject": subject,
        "text_body": text_body,
        "html_body": html_body,
    }


def week_select(request):
    """
    Step 1 of roster creation:
    - Manager selects a Monday date
    - If roster exists for that week, open it
    - Else create a new draft roster and open it
    """
    if request.method == "POST":
        form = WeeklyRosterSelectForm(request.POST)
        if form.is_valid():
            week_start_date = form.cleaned_data["week_start_date"]
            week_end_date = week_start_date + timedelta(days=6)

            roster, created = WeeklyRoster.objects.get_or_create(
                week_start_date=week_start_date,
                defaults={
                    "week_end_date": week_end_date,
                    "status": "draft",
                },
            )

            if created:
                messages.success(
                    request,
                    f"New weekly roster created for {week_start_date} to {week_end_date}.",
                )
            else:
                messages.success(
                    request,
                    f"Existing roster opened for {roster.week_start_date} to {roster.week_end_date}.",
                )
            request.session["active_roster_id"] = roster.id
            return redirect("roster:assign_week", roster_id=roster.id)
    else:
        form = WeeklyRosterSelectForm()

    return render(request, "roster/week_select.html", {"form": form})


def assign_week(request, roster_id):
    """
    Step 2 of roster creation:
    - Display employees and Monday-Sunday columns for selected roster
    - Save shifts for each employee/day
    - Optionally send shift emails after saving (checkbox)
    """
    roster = get_object_or_404(WeeklyRoster, pk=roster_id)
    employees = Employee.objects.filter(is_active=True).order_by("name")

    # Keep selected week in session for Payroll/Analytics/Shift Summary pages
    request.session["active_roster_id"] = roster.id

    # Build week days list (Mon-Sun)
    week_days = []
    current_date = roster.week_start_date
    for _ in range(7):
        week_days.append(current_date)
        current_date += timedelta(days=1)

    if request.method == "POST":
        saved_count = 0
        error_count = 0

        for emp in employees:
            for day in week_days:
                day_str = day.strftime("%Y-%m-%d")

                status_key = f"status_{emp.id}_{day_str}"
                start_key = f"start_{emp.id}_{day_str}"
                end_key = f"end_{emp.id}_{day_str}"
                break_key = f"break_{emp.id}_{day_str}"

                shift_status = request.POST.get(status_key, "off").strip()
                start_val = request.POST.get(start_key, "").strip()
                end_val = request.POST.get(end_key, "").strip()
                break_val = request.POST.get(break_key, "0").strip()

                # Parse break minutes safely
                try:
                    break_minutes = int(break_val) if break_val else 0
                    if break_minutes < 0:
                        break_minutes = 0
                except ValueError:
                    break_minutes = 0

                # Parse times only for assigned shifts
                start_time_obj = None
                end_time_obj = None

                if shift_status == "assigned":
                    try:
                        if start_val and end_val:
                            start_time_obj = datetime.strptime(start_val, "%H:%M").time()
                            end_time_obj = datetime.strptime(end_val, "%H:%M").time()
                        else:
                            # If assigned but missing time, fallback to off for now
                            shift_status = "off"
                            break_minutes = 0
                    except ValueError:
                        # Invalid time format
                        shift_status = "off"
                        start_time_obj = None
                        end_time_obj = None
                        break_minutes = 0
                else:
                    # off/leave/holiday should not store times
                    start_time_obj = None
                    end_time_obj = None
                    break_minutes = 0

                try:
                    # More reliable than update_or_create for recalculated fields like total_hours
                    shift_obj, _created = Shift.objects.get_or_create(
                        weekly_roster=roster,
                        employee=emp,
                        shift_date=day,
                        defaults={
                            "shift_status": "off",
                            "break_minutes": 0,
                        },
                    )

                    shift_obj.shift_status = shift_status
                    shift_obj.start_time = start_time_obj
                    shift_obj.end_time = end_time_obj
                    shift_obj.break_minutes = break_minutes

                    # This triggers clean() -> calculate_total_hours() -> save()
                    shift_obj.save()

                    saved_count += 1

                except Exception as e:
                    error_count += 1
                    print(
                        f"[SHIFT SAVE ERROR] emp={emp.id}, day={day}, "
                        f"status={shift_status}, start={start_val}, end={end_val}, "
                        f"break={break_minutes}, error={e}"
                    )

        # Optional: Send emails after saving if checkbox checked
        send_emails_after_save = request.POST.get("send_emails_after_save") == "1"
        email_sent_count = 0
        email_fail_count = 0

        if send_emails_after_save:
            for emp in employees:
                email_payload = _build_employee_shift_email_content(roster, emp)

                # Skip employees with no shifts in this week
                if not email_payload:
                    continue

                result = send_shift_email(
                    recipient_email=emp.email,
                    subject=email_payload["subject"],
                    text_body=email_payload["text_body"],
                    html_body=email_payload["html_body"],
                )

                if result["success"]:
                    email_sent_count += 1
                else:
                    email_fail_count += 1

        # Final user messages (save + email status)
        if error_count == 0:
            if send_emails_after_save:
                if email_fail_count == 0:
                    messages.success(
                        request,
                        f"Shifts saved successfully ({saved_count} cells). "
                        f"Emails sent to {email_sent_count} employee(s)."
                    )
                else:
                    messages.warning(
                        request,
                        f"Shifts saved successfully ({saved_count} cells), but email sending had issues. "
                        f"Emails sent: {email_sent_count}, failed: {email_fail_count}."
                    )
            else:
                messages.success(
                    request,
                    f"Shifts saved successfully. Total cells processed: {saved_count}."
                )
        else:
            if send_emails_after_save:
                messages.warning(
                    request,
                    f"Shifts saved with some issues. Saved: {saved_count}, Errors: {error_count}. "
                    f"Emails sent: {email_sent_count}, failed: {email_fail_count}."
                )
            else:
                messages.warning(
                    request,
                    f"Shifts saved with some issues. Saved: {saved_count}, Errors: {error_count}."
                )

        request.session["active_roster_id"] = roster.id
        return redirect("roster:assign_week", roster_id=roster.id)

    # GET request: fetch existing shifts for prefill
    existing_shifts = Shift.objects.filter(
        weekly_roster=roster,
        employee__in=employees,
        shift_date__range=[roster.week_start_date, roster.week_end_date],
    )

    # Dict key format: "employee_id|YYYY-MM-DD"
    shift_lookup_string_keys = {}
    for shift in existing_shifts:
        key = f"{shift.employee_id}|{shift.shift_date.strftime('%Y-%m-%d')}"
        shift_lookup_string_keys[key] = shift

    context = {
        "roster": roster,
        "employees": employees,
        "week_days": week_days,
        "shift_lookup_string_keys": shift_lookup_string_keys,
    }
    return render(request, "roster/assign_week.html", context)


def week_summary(request):
    """
    Show weekly roster summary for the latest roster.
    Later we can make this week-specific via URL parameter.
    """
    # roster = WeeklyRoster.objects.order_by("-week_start_date").first()
    
    active_roster_id = request.session.get("active_roster_id")
    if active_roster_id:
       roster = WeeklyRoster.objects.filter(id=active_roster_id).first()
    else:
       roster = WeeklyRoster.objects.order_by("-week_start_date").first()

    if not roster:
        messages.warning(request, "No weekly roster found. Please create a roster first.")
        return render(request, "roster/week_summary.html", {"roster": None})

    employees = Employee.objects.filter(is_active=True).order_by("name")

    # Build week days list (Mon-Sun)
    week_days = []
    current_date = roster.week_start_date
    for _ in range(7):
        week_days.append(current_date)
        current_date += timedelta(days=1)

    # Fetch shifts for this roster
    shifts = Shift.objects.filter(
        weekly_roster=roster,
        employee__in=employees,
        shift_date__range=[roster.week_start_date, roster.week_end_date]
    )

    # Lookup dict: "employee_id|YYYY-MM-DD" -> shift
    shift_lookup = {}
    for shift in shifts:
        key = f"{shift.employee_id}|{shift.shift_date.strftime('%Y-%m-%d')}"
        shift_lookup[key] = shift

    # Total weekly hours per employee
    employee_totals = {}
    for emp in employees:
        total = 0
        for day in week_days:
            key = f"{emp.id}|{day.strftime('%Y-%m-%d')}"
            shift = shift_lookup.get(key)
            if shift:
                total += float(shift.total_hours or 0)
        employee_totals[emp.id] = round(total, 2)
        
    payroll_rows = PayrollSummary.objects.filter(
           weekly_roster=roster,
           employee__in=employees
          )
    payroll_lookup = {p.employee_id: p for p in payroll_rows}
    
    analytics_rows = WorkforceAnalyticsResult.objects.filter(
        weekly_roster=roster,
        employee__in=employees
    )
    analytics_lookup = {a.employee_id: a for a in analytics_rows}
    
    context = {
        "roster": roster,
        "employees": employees,
        "week_days": week_days,
        "shift_lookup_string_keys": shift_lookup,
        "employee_totals": employee_totals,
        "payroll_lookup": payroll_lookup,
        "analytics_lookup": analytics_lookup,
    }
    return render(request, "roster/week_summary.html", context)
