from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testplans', '0003_delete_testplanpermissions_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testplanactivity',
            name='plan',
        ),
        migrations.RemoveField(
            model_name='testplanactivity',
            name='who',
        ),
        migrations.DeleteModel(
            name='TestPlanActivity',
        ),
    ]
