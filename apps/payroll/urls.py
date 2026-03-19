from django.urls import path
from . import views

app_name = "payroll"

urlpatterns = [
    path("calculate/<int:roster_id>/", views.calculate_payroll_for_roster, name="calculate_roster"),
    path("calculate/<int:roster_id>/", views.calculate_payroll_for_roster, name="calculate_roster"),
    path("summary/", views.payroll_summary, name="summary"),
]