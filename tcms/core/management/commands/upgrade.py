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
            answer = "x"

        self.stdout.write(
            """To finish the upgrade process, the following
management commands will be executed:

migrate
refresh_permissions
clean_orphan_obj_perms
remove_stale_contenttypes
delete_stale_attachments
delete_stale_comments
            """
        )

        self.stdout.write("\n1. Applying migrations:")
        call_command("migrate", verbosity=kwargs["verbosity"])

        self.stdout.write("\n2. Refreshing permissions:")
        call_command(
            "refresh_permissions",
            verbosity=kwargs["verbosity"],
            interactive=kwargs["interactive"],
        )

        self.stdout.write("\n3. Removes object permissions with not existing targets:")
        call_command("clean_orphan_obj_perms", verbosity=kwargs["verbosity"])

        self.stdout.write("\n4. Deleting stale content types:")
        call_command(
            "remove_stale_contenttypes",
            verbosity=kwargs["verbosity"],
            include_stale_apps=True,
            interactive=kwargs["interactive"],
        )

        self.stdout.write("\n5. Deleting stale attachments:")
        call_command(
            "delete_stale_attachments", verbosity=kwargs["verbosity"], answer=answer
        )

        self.stdout.write("\n6. Deleting stale comments:")
        call_command(
            "delete_stale_comments", verbosity=kwargs["verbosity"], answer=answer
        )

        self.stdout.write("Done.")
