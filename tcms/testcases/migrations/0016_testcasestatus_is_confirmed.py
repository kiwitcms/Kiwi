from django.db import migrations, models


def forwards(apps, schema_editor):
    test_case_status_model = apps.get_model("testcases", "TestCaseStatus")
    test_case_status_model.objects.filter(name="CONFIRMED").update(is_confirmed=True)


class Migration(migrations.Migration):

    dependencies = [
        ("testcases", "0015_add_summary_db_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="testcasestatus",
            name="is_confirmed",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
