from django.db import migrations


def forwards_add_perms(apps, schema_editor):
    """
    Adds permissions for this app to the group 'Tester'.
    This is useful in case that is an existing installation
    upgrading post 7.0.
    """
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")

    tester = group_model.objects.get(name="Tester")
    app_perms = permission_model.objects.filter(
        content_type__app_label__contains="bugs"
    )
    tester.permissions.add(*app_perms)


def backwards(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")
    tester = group_model.objects.get(name="Tester")
    app_perms = permission_model.objects.filter(
        content_type__app_label__contains="bugs"
    )
    tester.permissions.remove(*app_perms)


class Migration(migrations.Migration):
    dependencies = [
        ("bugs", "0001_initial"),
        ("core", "0001_squashed"),
    ]

    operations = [
        migrations.RunPython(forwards_add_perms, backwards),
    ]
