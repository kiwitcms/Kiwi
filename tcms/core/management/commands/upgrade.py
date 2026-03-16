from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Perform post-upgrade tasks for Kiwi TCMS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Automatic mode. Does not require user confirmation",
        )

    def handle(self, *args, **kwargs):
        answer = "y"
        if kwargs["interactive"]:
            answer = "n"

        self.stdout.write(
            """To finish the upgrade process, the following
management commands will be executed:

migrate
refresh_permissions
delete_stale_attachments
delete_stale_comments
            """
        )

        self.stdout.write("\n1. Applying migrations:")
        call_command(
            "migrate",
            verbosity=kwargs["verbosity"],
            interactive=kwargs["interactive"],
        )

        self.stdout.write("\n2. Refreshing permissions:")
        call_command(
            "refresh_permissions",
            verbosity=kwargs["verbosity"],
            interactive=kwargs["interactive"],
        )

        self.stdout.write("\n3. Deleting stale attachments:")
        call_command(
            "delete_stale_attachments", verbosity=kwargs["verbosity"], answer=answer
        )

        self.stdout.write("\n4. Deleting stale comments:")
        call_command(
            "delete_stale_comments", verbosity=kwargs["verbosity"], answer=answer
        )

        self.stdout.write("Done.")
