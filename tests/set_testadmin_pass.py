"""
    Allow testadmin to log in by setting its password
"""
from django.contrib.auth.models import User

testadmin = User.objects.get(username="testadmin")
testadmin.set_password("password")
testadmin.save()
