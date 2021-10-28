from django.db import models


class Property(models.Model):
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name}: {self.value}"
