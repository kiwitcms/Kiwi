# Renames TestCaseBug to Bug and
#         TestCaseBugSystem to BugSystem

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testcases', '0014_rename_testtag'),
    ]

    operations = [
        migrations.RenameModel('TestCaseBug', 'Bug'),
        migrations.RenameModel('TestCaseBugSystem', 'BugSystem'),

        migrations.AlterField(
            model_name='Bug',
            name='bug_system',
            field=models.ForeignKey(default=1, to='testcases.BugSystem',
                                    on_delete=models.CASCADE),
        ),
    ]
