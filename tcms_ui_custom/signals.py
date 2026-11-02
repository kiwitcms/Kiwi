from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.db.models.deletion import ProtectedError

from tcms.management.models import Product, Component, Priority, Tag, Version, Build
from tcms.testcases.models import TestCase, TestCaseStatus, Category
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun

def _prevent_delete_if_in_use(instance, related_objects, model_name):
    """Helper to raise ProtectedError if related objects exist."""
    if related_objects.exists():
        error_msg = f"Cannot delete {model_name} '{instance}' because it is currently in use by Test Cases."
        raise ProtectedError(error_msg, related_objects)

@receiver(pre_delete, sender=Product)
def protect_product(sender, instance, **kwargs):
    test_cases = TestCase.objects.filter(component__product=instance).distinct()
    _prevent_delete_if_in_use(instance, test_cases, "Project")

@receiver(pre_delete, sender=Component)
def protect_component(sender, instance, **kwargs):
    test_cases = TestCase.objects.filter(component=instance)
    _prevent_delete_if_in_use(instance, test_cases, "Module")

@receiver(pre_delete, sender=TestCaseStatus)
def protect_status(sender, instance, **kwargs):
    test_cases = TestCase.objects.filter(case_status=instance)
    _prevent_delete_if_in_use(instance, test_cases, "Status")

@receiver(pre_delete, sender=Priority)
def protect_priority(sender, instance, **kwargs):
    test_cases = TestCase.objects.filter(priority=instance)
    _prevent_delete_if_in_use(instance, test_cases, "Priority")

@receiver(pre_delete, sender=Tag)
def protect_tag(sender, instance, **kwargs):
    test_cases = TestCase.objects.filter(tag=instance)
    _prevent_delete_if_in_use(instance, test_cases, "Tag")

@receiver(pre_delete, sender=Category)
def protect_category(sender, instance, **kwargs):
    test_cases = TestCase.objects.filter(category=instance)
    _prevent_delete_if_in_use(instance, test_cases, "Category")

@receiver(pre_delete, sender=Version)
def protect_version(sender, instance, **kwargs):
    _prevent_delete_if_in_use(instance, TestPlan.objects.filter(product_version=instance), "Version")

@receiver(pre_delete, sender=Build)
def protect_build(sender, instance, **kwargs):
    _prevent_delete_if_in_use(instance, TestRun.objects.filter(build=instance), "Build")
