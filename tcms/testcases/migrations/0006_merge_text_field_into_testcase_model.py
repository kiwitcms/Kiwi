from django.db import migrations, models


def convert_test_case_text(test_case_text):
    return """**Setup:**
%s

**Actions:**
%s

**Expected result:**
%s

**Breakdown:**
%s
""" % (test_case_text.setup,
        test_case_text.action,
        test_case_text.effect,
        test_case_text.breakdown)


def forward_copy_data(apps, schema_editor):
    TestCase = apps.get_model('testcases', 'TestCase')
    TestCaseText = apps.get_model('testcases', 'TestCaseText')
    HistoricalTestCase = apps.get_model('testcases', 'HistoricalTestCase')

    for test_case in TestCase.objects.all():
        latest_text = TestCaseText.objects.filter(case=test_case.pk).order_by('-pk').first()
        if latest_text:
            test_case.case_text = convert_test_case_text(latest_text)
            test_case.save()
            # b/c the above will not generate history
            history = HistoricalTestCase.objects.filter(
                        case_id=test_case.pk
                      ).order_by('-history_id').first()
            history.case_text = test_case.case_text
            history.save()


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0005_remove_unused_fields'),
    ]

    operations = [
        # add new field to hold TC text but use a temporary name
        # b/c `text` is also the name of the pre-existing reverse relationship
        migrations.AddField(
            model_name='historicaltestcase',
            name='case_text',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='testcase',
            name='case_text',
            field=models.TextField(blank=True),
        ),

        # copy the data from the related model
        migrations.RunPython(forward_copy_data),

        # remove the related model
        migrations.RemoveField(
            model_name='testcasetext',
            name='author',
        ),
        migrations.DeleteModel(
            name='TestCaseText',
        ),

        # rename the new field to what is inside the model source
        migrations.RenameField(
            model_name='historicaltestcase',
            old_name='case_text',
            new_name='text',
        ),
        migrations.RenameField(
            model_name='testcase',
            old_name='case_text',
            new_name='text',
        ),
    ]
