# Renames TCMSEnv* to Env*

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testplans', '0007_add_related_name_to_testplan'),
        ('management', '0007_rename_env'),
    ]

    operations = [
        migrations.RenameModel('TCMSEnvPlanMap', 'EnvPlanMap'),

        migrations.AlterField(
            model_name='EnvPlanMap',
            name='group',
            field=models.ForeignKey(to='management.EnvGroup',
                                    on_delete=models.CASCADE)),

        migrations.AlterField(
            model_name='TestPlan',
            name='env_group',
            field=models.ManyToManyField(to='management.EnvGroup',
                                         through='testplans.EnvPlanMap')),
    ]
