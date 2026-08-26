import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import DEFAULT_DB_ALIAS, connections


class Command(BaseCommand):
    help = "Performs initial setup of *NEW* Kiwi TCMS installation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            choices=tuple(connections),
            help='Specifies the database to use. Default is "default".',
        )

    def handle(self, *args, **kwargs):
        self.stdout.write("\n1. Applying migrations:")
        call_command("migrate", f"--verbosity={kwargs['verbosity']}")

        self.stdout.write("\n2. Creating superuser:")
        call_command("createsuperuser", f"--verbosity={kwargs['verbosity']}")

        self.stdout.write("\n3. Setting the domain name:")
        domain = os.environ.get("KIWI_TENANTS_DOMAIN")
        if not domain:
            domain = input("Enter Kiwi TCMS domain: ")  # nosec
        call_command("set_domain", domain=domain)

        if "tcms_tenants" in settings.INSTALLED_APPS:
            self.stdout.write("\n4. Creating public & empty tenants:")
            call_command(
                "initialize_tenants",
                f"--verbosity={kwargs['verbosity']}",
                "--domain",
                domain,
            )

        self.stdout.write("\n5. Setting permissions:")
        call_command("refresh_permissions", f"--verbosity={kwargs['verbosity']}")

        self.stdout.write("\nInitial setup finished.")
