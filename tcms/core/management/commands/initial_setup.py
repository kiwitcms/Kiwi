import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Performs initial setup of *NEW* Kiwi TCMS installation."

    def handle(self, *args, **kwargs):

        self.stdout.write("\n1. Applying migrations:")
        call_command("migrate", f"--verbosity={kwargs['verbosity']}")

        self.stdout.write("\n2. Creating superuser:")
        call_command("createsuperuser", f"--verbosity={kwargs['verbosity']}")

        self.stdout.write("\n3. Setting the domain name:")
        domain = input("Enter Kiwi TCMS domain: ")  # nosec
        call_command("set_domain", domain=domain)

        if "tcms_tenants" in settings.INSTALLED_APPS:
            self.stdout.write("\n4. Creating public & empty tenants:")
            superuser = get_user_model().objects.filter(is_superuser=True).first()
            paid_until = timezone.now() + datetime.timedelta(days=100 * 365)
            call_command(
                "create_tenant",
                f"--verbosity={kwargs['verbosity']}",
                "--schema_name",
                "public",
                "--name",
                "Public tenant",
                "--paid_until",
                paid_until.isoformat(),
                "--publicly_readable",
                False,
                "--owner_id",
                superuser.pk,
                "--organization",
                "Testing department",
                "--domain-domain",
                domain,
                "--domain-is_primary",
                True,
            )

            # a special tenant for cloning
            call_command(
                "create_tenant",
                f"--verbosity={kwargs['verbosity']}",
                "--schema_name",
                "empty",
                "--name",
                "Cloning Template",
                "--paid_until",
                paid_until.isoformat(),
                "--publicly_readable",
                False,
                "--owner_id",
                superuser.pk,
                "--organization",
                "Kiwi TCMS",
                "--domain-domain",
                "empty.example.org",
                "--domain-is_primary",
                True,
            )

        self.stdout.write("\n5. Setting permissions:")
        call_command("refresh_permissions", f"--verbosity={kwargs['verbosity']}")

        self.stdout.write("\nInitial setup finished.")
