from django.core.management import call_command
from django.core.management.base import BaseCommand


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

        self.stdout.write("\nInitial setup finished.")
