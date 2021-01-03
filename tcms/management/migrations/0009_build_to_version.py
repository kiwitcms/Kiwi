import json

from django.conf import settings
from django.db import migrations, models
from django.forms.models import model_to_dict


def forwards(apps, schema_editor):
    build_model = apps.get_model("management", "Build")
    version_model = apps.get_model("management", "Version")

    for build in build_model.objects.all():
        # backup current values
        file_name = "kiwitcms-management-migration-0009-build_to_version-%d" % build.pk
        file_name = settings.TEMP_DIR / file_name

        with file_name.open("w") as outfile:
            json.dump(model_to_dict(build), outfile)

        # then adjust the value for the `version` field
        qset = version_model.objects.filter(product=build.product)
        version = qset.filter(value="unspecified").first()

        # if Version "unspecified" has been removed then pin builds
        # to the first version found for the same product
        if not version:
            version = qset.first()

        build.version = version.pk
        build.save()


def backwards(apps, schema_editor):
    build_model = apps.get_model("management", "Build")

    for build in build_model.objects.all():
        # restore product field value
        file_name = "kiwitcms-management-migration-0009-build_to_version-%d" % build.pk
        file_name = settings.TEMP_DIR / file_name

        with file_name.open("r") as infile:
            data = json.load(infile)
            build.product = data["product"]
            build.save()


class Migration(migrations.Migration):

    dependencies = [
        ("management", "0008_increase_product_name_size"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="build",
            options={
                "ordering": ["name"],
                "verbose_name": "Build",
                "verbose_name_plural": "Builds",
            },
        ),
        # add new `version` field as integer
        migrations.AddField(
            model_name="build",
            name="version",
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        # assign appropriate values from other DB records
        migrations.RunPython(forwards, backwards),
        # convert `version` field to FK
        migrations.AlterField(
            model_name="build",
            name="version",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="build",
                to="management.version",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="build",
            unique_together={("version", "name")},
        ),
        migrations.RemoveField(
            model_name="build",
            name="product",
        ),
    ]
