from django.db import migrations


def forward_copy_data(apps, schema_editor):
    bug_model = apps.get_model('testcases', 'Bug')
    link_reference_model = apps.get_model('linkreference', 'LinkReference')

    for bug in bug_model.objects.all():
        if not bug.case_run_id:
            continue

        link_reference_model.objects.create(
            execution_id=bug.case_run_id,
            name="%s %s" % (bug.bug_system.name, bug.bug_id),
            url=bug.bug_system.url_reg_exp % bug.bug_id,
            is_defect=True,
        )


def backward_empty_callable(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0009_populate_missing_text_history'),
        ('linkreference', '0002_update_fields'),
    ]

    operations = [
        # copy the data from the related model
        migrations.RunPython(forward_copy_data, backward_empty_callable),

        migrations.DeleteModel(
            name='Bug',
        ),
    ]
