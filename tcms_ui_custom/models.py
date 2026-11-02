from django.db import models
from django.contrib.auth.models import User
from tcms.testplans.models import TestPlan
from tcms.testcases.models import TestCase

class TestPlanMetadata(models.Model):
    STATUS_CHOICES = (
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )

    testplan = models.OneToOneField(TestPlan, on_delete=models.CASCADE, related_name='custom_metadata')
    description = models.TextField(blank=True, null=True)
    environment = models.CharField(max_length=255, blank=True, null=True)
    target_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    resources = models.ManyToManyField(User, blank=True)
    out_of_scope_cases = models.ManyToManyField(TestCase, blank=True, related_name='out_of_scope_in_plans')

    def __str__(self):
        return f"Metadata for {self.testplan.name}"
