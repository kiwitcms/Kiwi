import json

from django.conf import settings
from django.db import migrations, models
from django.forms.models import model_to_dict


def forwards_store_data(apps, schema_editor):
    bug_system_model = apps.get_model("testcases", "BugSystem")

    for bug_system in bug_system_model.objects.all():
        file_name = "kiwitcms-testcases-migration-0011-BugSystem-%d" % bug_system.pk
        bug_file = settings.TEMP_DIR / file_name

        with bug_file.open("w") as outfile:
            json.dump(model_to_dict(bug_system), outfile)


def backwards_restore_data(apps, schema_editor):
    bug_system_model = apps.get_model("testcases", "BugSystem")

    for file in settings.TEMP_DIR.glob("kiwitcms-testcases-migration-0011-BugSystem-*"):
        with file.open("r") as infile:
            data = json.load(infile)
            bug_system = bug_system_model(**data)
            bug_system.save()


class Migration(migrations.Migration):

    dependencies = [
        ("testcases", "0010_remove_bug"),
    ]

    operations = [
        # make these 2 fields null=True so they can be restored in the reverse migration
        # once these 2 operations are reversed the fields should become once again NOT NULL
        migrations.AlterField(
            model_name="bugsystem",
            name="validate_reg_exp",
            field=models.CharField(
                max_length=128,
                help_text="A valid JavaScript regular " "expression such as ^\\d$",
                verbose_name="RegExp for ID validation",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="bugsystem",
            name="url_reg_exp",
            field=models.CharField(
                max_length=8192,
                help_text="A valid Python format string such "
                "as http://bugs.example.com/%s",
                verbose_name="URL format string",
                null=True,
            ),
        ),
        migrations.RunPython(forwards_store_data, backwards_restore_data),
        migrations.RemoveField(
            model_name="bugsystem",
            name="description",
        ),
        migrations.RemoveField(
            model_name="bugsystem",
            name="url_reg_exp",
        ),
        migrations.RemoveField(
            model_name="bugsystem",
            name="validate_reg_exp",
        ),
    ]
