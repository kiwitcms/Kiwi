import json

from django.conf import settings
from django.db import migrations, models
from django.forms.models import model_to_dict


def convert_test_case_text(test_case_text):
    return """**Setup:**
%s

**Actions:**
%s

**Expected result:**
%s

**Breakdown:**
%s
""" % (
        test_case_text.setup,
        test_case_text.action,
        test_case_text.effect,
        test_case_text.breakdown,
    )


def forward_copy_data(apps, schema_editor):
    test_case_model = apps.get_model("testcases", "TestCase")
    test_case_text_model = apps.get_model("testcases", "TestCaseText")
    historical_test_case_model = apps.get_model("testcases", "HistoricalTestCase")

    for test_case in test_case_model.objects.all():
        latest_text = (
            test_case_text_model.objects.filter(case=test_case.pk)
            .order_by("-pk")
            .first()
        )
        if latest_text:
            file_name = (
                "kiwitcms-testcases-migrations-0006-TestCaseText-%d" % latest_text.pk
            )
            test_case_file = settings.TEMP_DIR / file_name
            with test_case_file.open("w") as outfile:
                json.dump(model_to_dict(latest_text), outfile)

            test_case.case_text = convert_test_case_text(latest_text)
            test_case.save()
            # b/c the above will not generate history
            history = (
                historical_test_case_model.objects.filter(case_id=test_case.pk)
                .order_by("-history_id")
                .first()
            )
            history.case_text = test_case.case_text
            history.save()


def backward_restore_data(apps, schema_editor):
    test_case_text_model = apps.get_model("testcases", "TestCaseText")

    for file in settings.TEMP_DIR.glob(
        "kiwitcms-testcases-migrations-0006-TestCaseText-*"
    ):
        with file.open("r") as infile:
            data = json.load(infile)
            test_case_text = test_case_text_model(**data)
            test_case_text.save()


class Migration(migrations.Migration):

    dependencies = [
        ("testcases", "0005_remove_unused_fields"),
    ]

    operations = [
        # add new field to hold TC text but use a temporary name
        # b/c `text` is also the name of the pre-existing reverse relationship
        migrations.AddField(
            model_name="historicaltestcase",
            name="case_text",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="testcase",
            name="case_text",
            field=models.TextField(blank=True),
        ),
        # copy the data from the related model
        migrations.RunPython(forward_copy_data, backward_restore_data),
        # remove the related model
        migrations.RemoveField(
            model_name="testcasetext",
            name="author",
        ),
        migrations.DeleteModel(
            name="TestCaseText",
        ),
        # rename the new field to what is inside the model source
        migrations.RenameField(
            model_name="historicaltestcase",
            old_name="case_text",
            new_name="text",
        ),
        migrations.RenameField(
            model_name="testcase",
            old_name="case_text",
            new_name="text",
        ),
    ]
