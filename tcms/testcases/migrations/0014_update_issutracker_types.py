from django.db import migrations


def forwards(apps, schema_editor):
    bug_system_model = apps.get_model("testcases", "BugSystem")

    for record in bug_system_model.objects.all():
        if record.tracker_type:
            record.tracker_type = "tcms.issuetracker.types.%s" % record.tracker_type
            record.save()


def backwards(apps, schema_editor):
    bug_system_model = apps.get_model("testcases", "BugSystem")

    for record in bug_system_model.objects.all():
        if record.tracker_type.startswith("tcms.issuetracker.types."):
            record.tracker_type = record.tracker_type.replace(
                "tcms.issuetracker.types.", ""
            )
            record.save()


class Migration(migrations.Migration):

    dependencies = [
        ("testcases", "0013_remove_autofield"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
