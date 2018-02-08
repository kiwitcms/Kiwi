# Rename TestPlanType to PlanType

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testplans', '0008_rename_env'),
    ]

    operations = [
        migrations.RenameModel('TestPlanType', 'PlanType'),

        migrations.AlterField(
            model_name='TestPlan',
            name='type',
            field=models.ForeignKey(to='testplans.PlanType', on_delete=models.CASCADE)),

    ]
