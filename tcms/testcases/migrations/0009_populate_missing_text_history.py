from django.db import migrations


def forward_copy_data(apps, schema_editor):
    TestCase = apps.get_model('testcases', 'TestCase')
    HistoricalTestCase = apps.get_model('testcases', 'HistoricalTestCase')

    for test_case in TestCase.objects.all():
        history = HistoricalTestCase.objects.filter(
                    case_id=test_case.pk
                  ).order_by('-history_id').first()

        # In 0006_merge_text_field_into_testcase_model we may have
        # failed to save the text into the history record leaving
        # historical records with text == None.
        # If the TC was not modified since then we try to fix the last
        # historical record
        if test_case.text and not history.text:
            history.text = test_case.text
            history.save()


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0008_notifications_default_true'),
    ]

    operations = [
        # copy the data from the related model
        migrations.RunPython(forward_copy_data),
    ]
