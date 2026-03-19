from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("run/<int:roster_id>/", views.run_analytics_for_roster, name="run_roster"),
    path("summary/", views.analytics_summary, name="summary"),
]