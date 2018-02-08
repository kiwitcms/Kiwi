# Renames TestTag to Tag

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testcases', '0013_rename_testcasecategory_to_casecategory'),
        ('management', '0008_rename_testtag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='TestCaseTag',
            name='tag',
            field=models.ForeignKey(to='management.Tag', on_delete=models.CASCADE),
        ),

        migrations.AlterField(
            model_name='TestCase',
            name='tag',
            field=models.ManyToManyField(related_name='case',
                                         through='testcases.TestCaseTag',
                                         to='management.Tag'),
        ),
    ]
