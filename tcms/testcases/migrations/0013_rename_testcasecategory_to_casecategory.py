# Renames TestCaseCategory to Category

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testcases', '0012_alter_related_name_for_testcase'),
    ]

    operations = [
        migrations.RenameModel('TestCaseCategory', 'Category'),

        migrations.AlterField(
            model_name='TestCase',
            name='category',
            field=models.ForeignKey(related_name='category_case', to='testcases.Category',
                                    on_delete=models.CASCADE)),

    ]
