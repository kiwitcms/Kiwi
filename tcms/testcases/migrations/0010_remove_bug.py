import glob
import json

from django.db import migrations


def forward_copy_data(apps, schema_editor):
    bug_model = apps.get_model('testcases', 'Bug')
    link_reference_model = apps.get_model('linkreference', 'LinkReference')
    link_reference_ids = []

    for bug in bug_model.objects.all():
        file_name = '/tmp/kiwitcms-testcases-migrations-\
0010-Bug-%d' % bug.pk  # nosec:B108:hardcoded_tmp_directory
        with open(file_name, 'w') as outfile:
            json.dump(bug.serialize(), outfile)

        if not bug.case_run_id:
            continue

        link_reference = link_reference_model.objects.create(
            execution_id=bug.case_run_id,
            name="%s %s" % (bug.bug_system.name, bug.bug_id),
            url=bug.bug_system.url_reg_exp % bug.bug_id,
            is_defect=True,
        )
        link_reference_ids.append(link_reference.pk)

    link_reference_ids_file_name = '/tmp/kiwitcms-testcases-migrations-0010-\
new-LinkReference-IDs'  # nosec:B108:hardcoded_tmp_directory
    with open(link_reference_ids_file_name, 'w') as link_reference_ids_file:
        json.dump(link_reference_ids, link_reference_ids_file)


def backward_restore_data(apps, schema_editor):
    bug_model = apps.get_model('testcases', 'Bug')
    link_reference_model = apps.get_model('linkreference', 'LinkReference')

    for file_name in glob.glob(
            '/tmp/kiwitcms-testcases-migrations-0010-Bug-*'  # nosec:B108:hardcoded_tmp_directory
    ):
        with open(file_name, 'r') as infile:
            data = json.loads(infile)
            bug = bug_model(**data)
            bug.save()

    link_reference_ids_file_name = '/tmp/kiwitcms-testcases-migrations-0010-\
new-LinkReference-IDs'  # nosec:B108:hardcoded_tmp_directory
    with open(link_reference_ids_file_name, 'r') as link_reference_ids_file:
        link_reference_ids = json.load(link_reference_ids_file)
        link_reference_model.objects.filter(
            pk__in=link_reference_ids.delete())


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0009_populate_missing_text_history'),
        ('linkreference', '0002_update_fields'),
    ]

    operations = [
        # copy the data from the related model
        migrations.RunPython(forward_copy_data, backward_restore_data),

        migrations.DeleteModel(
            name='Bug',
        ),
    ]
