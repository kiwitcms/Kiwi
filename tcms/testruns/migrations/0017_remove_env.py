# Generated by Django 2.1 on 2018-08-21 13:58

from django.db import migrations


def forwards_convert(apps, schema_editor):
    """
        Converts all EnvValue(s) to Tag(s)
    """
    Tag = apps.get_model('management', 'Tag')
    TestRun = apps.get_model('testruns', 'TestRun')
    TestRunTag = apps.get_model('testruns', 'TestRunTag')

    for test_run in TestRun.objects.all():
        for env_value in test_run.env_value.all():
            tag_name = "%s: %s" % (env_value.property.name, env_value.value)
            tag, _ = Tag.objects.get_or_create(name=tag_name)

            # do it like this b/c the above TestRun class is a __fake__
            # which doesn't have the add_tag() method
            TestRunTag.objects.get_or_create(run=test_run, tag=tag)


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0016_remove_auto_update_run_status'),
    ]

    operations = [
        # note: in managament/migrations/0013_remove_env.py we specify the dependency
        # order and the current migration is executed before env related models are
        # removed
        migrations.RunPython(forwards_convert),

        migrations.RemoveField(
            model_name='historicaltestcaserun',
            name='environment_id',
        ),
        migrations.RemoveField(
            model_name='historicaltestrun',
            name='environment_id',
        ),
        migrations.RemoveField(
            model_name='testcaserun',
            name='environment_id',
        ),
        migrations.RemoveField(
            model_name='testrun',
            name='environment_id',
        ),

        migrations.RemoveField(
            model_name='envrunvaluemap',
            name='run',
        ),
        migrations.RemoveField(
            model_name='envrunvaluemap',
            name='value',
        ),
        migrations.RemoveField(
            model_name='testrun',
            name='env_value',
        ),
        migrations.DeleteModel(
            name='EnvRunValueMap',
        ),
    ]
