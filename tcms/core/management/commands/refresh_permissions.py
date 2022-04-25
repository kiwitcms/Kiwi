from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

from tcms.utils.permissions import assign_default_group_permissions


class Command(BaseCommand):
    help = (
        "Refresh permissions for Tester group "
        "(set by DEFAULT_GROUPS setting) and remove stale ones."
    )

    group_model = Group
    admin_permissions_filter = {}
    tester_permissions_filter = {}

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Automatic mode. Does not require user input",
        )

    def handle(self, *args, **kwargs):
        """
        This is the command entry-point!
        """
        self.execute_commands(*args, **kwargs)

        if "tenant_groups" in settings.INSTALLED_APPS:
            call_command(
                "refresh_tenant_permissions",
                *args,
                **kwargs,
            )

    def execute_commands(self, *args, **kwargs):
        """
        This is the actual implementation. Can be overriden by inherited classes.
        """
        output = None
        if kwargs["verbosity"]:
            output = self.stdout

        call_command("update_permissions", f"--verbosity={kwargs['verbosity']}")

        # Assign permissions to Tester group
        if output:
            self.stdout.write("\nSetting up missing permissions")
        assign_default_group_permissions(
            output=output,
            refresh_all=True,
            group_model=self.group_model,
            admin_permissions_filter=self.admin_permissions_filter,
            tester_permissions_filter=self.tester_permissions_filter,
        )
        if output:
            self.stdout.write("Done.")

        # Removing stale permissions
        if output:
            self.stdout.write("\nRemoving stale permissions")
        call_command(
            "remove_stale_contenttypes",
            "--include-stale-apps",
            f"--verbosity={kwargs['verbosity']}",
            interactive=kwargs["interactive"],
        )
        call_command("clean_orphan_obj_perms", f"--verbosity={kwargs['verbosity']}")
        if output:
            self.stdout.write("Done.")
