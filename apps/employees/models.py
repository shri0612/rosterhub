from django.db import models


class Employee(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    age = models.PositiveIntegerField()
    department = models.CharField(max_length=100, blank=True, null=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default="full_time"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.email})"