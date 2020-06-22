from django.db import models


class TestPerson(models.Model):
    name = models.CharField(max_length=10)
