from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Employee
from .forms import EmployeeForm


def employee_list(request):
    employees = Employee.objects.all().order_by("name")
    return render(request, "employees/list.html", {"employees": employees})


def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee added successfully.")
            return redirect("employees:list")
    else:
        form = EmployeeForm()

    return render(request, "employees/form.html", {
        "form": form,
        "page_heading": "Add Employee",
        "submit_label": "Create Employee",
    })


def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee updated successfully.")
            return redirect("employees:list")
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "employees/form.html", {
        "form": form,
        "page_heading": "Edit Employee",
        "submit_label": "Update Employee",
        "employee": employee,
    })


def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        employee.delete()
        messages.success(request, "Employee deleted successfully.")
        return redirect("employees:list")

    return render(request, "employees/confirm_delete.html", {"employee": employee})