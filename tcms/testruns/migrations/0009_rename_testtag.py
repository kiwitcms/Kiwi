# Renames TestTag to Tag

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testruns', '0008_rename_env'),
        ('management', '0008_rename_testtag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='TestRunTag',
            name='tag',
            field=models.ForeignKey(to='management.Tag', on_delete=models.CASCADE)
        ),

        migrations.AlterField(
            model_name='TestRun',
            name='tag',
            field=models.ManyToManyField(related_name='run',
                                         through='testruns.TestRunTag',
                                         to='management.Tag'),
        ),
    ]
