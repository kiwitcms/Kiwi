import json

from django.conf import settings
from django.db import migrations
from django.forms.models import model_to_dict


def forward_copy_data(apps, schema_editor):
    bug_model = apps.get_model("testcases", "Bug")
    link_reference_model = apps.get_model("linkreference", "LinkReference")
    link_reference_ids = []

    for bug in bug_model.objects.all():
        bug_file_name = "kiwitcms-testcases-migrations-0010-Bug-%d" % bug.pk
        bug_file = settings.TEMP_DIR / bug_file_name
        with bug_file.open("w") as outfile:
            json.dump(model_to_dict(bug), outfile)

        if not bug.case_run_id:
            continue

        link_reference = link_reference_model.objects.create(
            execution_id=bug.case_run_id,
            name="%s %s" % (bug.bug_system.name, bug.bug_id),
            url=bug.bug_system.url_reg_exp % bug.bug_id,
            is_defect=True,
        )
        link_reference_ids.append(link_reference.pk)

    link_reference_ids_file_name = (
        "kiwitcms-testcases-migrations-0010-new-LinkReference-IDs"
    )
    link_reference_ids_file = settings.TEMP_DIR / link_reference_ids_file_name
    with link_reference_ids_file.open("w") as outfile:
        json.dump(link_reference_ids, outfile)


def backward_restore_data(apps, schema_editor):
    bug_model = apps.get_model("testcases", "Bug")
    link_reference_model = apps.get_model("linkreference", "LinkReference")

    for file in settings.TEMP_DIR.glob("kiwitcms-testcases-migrations-0010-Bug-*"):
        with file.open("r") as infile:
            data = json.load(infile)
            bug = bug_model(**data)
            bug.save()

    link_reference_ids_file_name = (
        "kiwitcms-testcases-migrations-0010-new-LinkReference-IDs"
    )
    link_reference_ids_file = settings.TEMP_DIR / link_reference_ids_file_name
    with link_reference_ids_file.open("r") as infile:
        link_reference_ids = json.load(infile)
        link_reference_model.objects.filter(pk__in=link_reference_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("testcases", "0009_populate_missing_text_history"),
        ("linkreference", "0002_update_fields"),
    ]

    operations = [
        # copy the data from the related model
        migrations.RunPython(forward_copy_data, backward_restore_data),
        migrations.DeleteModel(
            name="Bug",
        ),
    ]
