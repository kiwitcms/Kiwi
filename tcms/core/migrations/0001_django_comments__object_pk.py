# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class DjangoCommentsAlterField(migrations.AlterField):
    """Custom migration operation which alters `django_comments`!

    We need this because when Django is executing migrations it will record
    them as app_label|migration_name in the database.

    If we override `Migration.app_label` to 'django_comments' this
    gives us access to the Comment model, however Django records the
    migration as django_comments|0001_django_comments__object_pk instead
    of core|0001_django_comments__object_pk. This means the migration will
    be shown as not appliead the next time!!!

    If we don't override Migration.app_label we don't get access to the
    django_comments.models.Comment model !!!

    The problem is that we're trying to alter a 3rd party model which
    doesn't belong to this application hence this class.
    """
    def state_forwards(self, app_label, state):
        super(DjangoCommentsAlterField, self).state_forwards('django_comments', state)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        super(DjangoCommentsAlterField, self).database_forwards('django_comments', schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        super(DjangoCommentsAlterField, self).database_backwards('django_comments', schema_editor, from_state, to_state)


class Migration(migrations.Migration):

    dependencies = [
        ('django_comments', '__latest__'),
    ]

    operations = [
        DjangoCommentsAlterField('comment', 'object_pk', models.IntegerField())
    ]
