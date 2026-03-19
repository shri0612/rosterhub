from django.urls import path
from . import views

app_name = "roster"

urlpatterns = [
    path("week-select/", views.week_select, name="week_select"),
    path("assign/<int:roster_id>/", views.assign_week, name="assign_week"),
    path("week-summary/", views.week_summary, name="week_summary"),
]