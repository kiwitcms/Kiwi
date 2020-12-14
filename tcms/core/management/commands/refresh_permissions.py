from django.core.management import call_command
from django.core.management.base import BaseCommand

from tcms.utils.permissions import assign_default_group_permissions


class Command(BaseCommand):
    help = (
        "Refresh permissions for Tester group "
        "(set by DEFAULT_GROUPS setting) and remove stale ones."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Automatic mode. Does not require user input",
        )

    def handle(self, *args, **kwargs):
        output = None
        if kwargs["verbosity"]:
            output = self.stdout

        call_command("update_permissions", "--verbosity=%i" % kwargs["verbosity"])

        # Assign permissions to Tester group
        if output:
            self.stdout.write("\nSetting up missing permissions")
        assign_default_group_permissions(output=output, refresh_all=True)
        if output:
            self.stdout.write("Done.")

        # Removing stale permissions
        if output:
            self.stdout.write("\nRemoving stale permissions")
        call_command(
            "remove_stale_contenttypes",
            "--include-stale-apps",
            "--verbosity=%i" % kwargs["verbosity"],
            interactive=kwargs["interactive"],
        )
        call_command("clean_orphan_obj_perms", "--verbosity=%i" % kwargs["verbosity"])
        if output:
            self.stdout.write("Done.")
