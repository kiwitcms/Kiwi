from django.db import migrations, models


class Migration(migrations.Migration):

    operations = [

        migrations.CreateModel(
            "TestPerson",
            [
                ("id", models.AutoField(primary_key=True)),
                ("name", models.CharField(max_length=10)),
            ],
        ),
    ]
