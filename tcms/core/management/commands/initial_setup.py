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
        call_command("migrate", "--verbosity=%i" % kwargs["verbosity"])

        self.stdout.write("\n2. Creating superuser:")
        call_command("createsuperuser", "--verbosity=%i" % kwargs["verbosity"])

        self.stdout.write("\n3. Setting the domain name:")
        domain = input("Enter Kiwi TCMS domain: ")  # nosec
        call_command("set_domain", domain=domain)

        self.stdout.write("\n4. Setting permissions:")
        call_command("refresh_permissions", "--verbosity=%i" % kwargs["verbosity"])

        if "tcms_tenants" in settings.INSTALLED_APPS:
            self.stdout.write("\n5. Creating the public tenant:")
            superuser = get_user_model().objects.filter(is_superuser=True).first()
            paid_until = timezone.now() + datetime.timedelta(days=100 * 365)
            call_command(
                "create_tenant",
                "--verbosity=%i" % kwargs["verbosity"],
                "-schema_name public",
                "--name 'Public tenant'",
                "--paid_until %s" % paid_until.isoformat(),
                "--publicly_readable False",
                "--owner_id %i" % superuser.pk,
                "--organization 'Testing department'",
                "--domain-domain %s" % domain,
                "--domain-is_primary True",
            )

        self.stdout.write("\nInitial setup finished.")
