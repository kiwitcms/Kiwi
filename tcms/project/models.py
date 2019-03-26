from django.db import models


class Project(models.Model):
    name = models.CharField(blank=False, null=False, max_length=128)
    enabled = models.BooleanField(default=False)
    users = models.ManyToManyField('auth.User', blank=True)
    testplans = models.ManyToManyField('testplans.TestPlan', blank=True)

    @classmethod
    def get_projects_enabled(cls):
        return cls.objects.get(enabled=True)

    @classmethod
    def get_projects_all(cls):
        return cls.objects.all()

    @classmethod
    def get_user_enabled_projects(cls, user):
        return cls.objects.filter(users=user, enabled=True)
