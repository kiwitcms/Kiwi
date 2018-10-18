# Renames TestTag to Tag

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testplans', '0002_squashed'),
        ('management', '0008_rename_testtag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='TestPlanTag',
            name='tag',
            field=models.ForeignKey(to='management.Tag', on_delete=models.CASCADE)
        ),

        migrations.AlterField(
            model_name='TestPlan',
            name='tag',
            field=models.ManyToManyField(related_name='plan',
                                         through='testplans.TestPlanTag',
                                         to='management.Tag'),
        ),
    ]
