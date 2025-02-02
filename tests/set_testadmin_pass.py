"""
Allow testadmin to log in by setting its password
"""

from django.contrib.auth.models import User

from tcms.management.models import Classification, Product, Version
from tcms.testplans.models import PlanType, TestPlan

testadmin = User.objects.get(username="testadmin")
testadmin.set_password("password")
testadmin.save()


classification, _ = Classification.objects.get_or_create(name="core products")
product, _ = Product.objects.get_or_create(
    name="Kiwi TCMS", classification=classification
)
version, _ = Version.objects.get_or_create(value="devel", product=product)

TestPlan.objects.create(
    name="Check if uploading files works",
    product=product,
    product_version=version,
    type=PlanType.objects.first(),
    author=testadmin,
)
