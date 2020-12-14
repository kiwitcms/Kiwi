from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Sets the domain of Kiwi TCMS instance. "
        "If no arguments given returns current domain."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "domain",
            nargs="?",
            default=None,
            help="The domain of Kiwi TCMS instance",
        )

    def handle(self, *args, **kwargs):
        site = Site.objects.get(id=settings.SITE_ID)
        if not kwargs["domain"]:
            self.stdout.write("%s" % (site.domain))
            return
        site.domain = kwargs["domain"]
        site.name = "Kiwi TCMS"
        site.save()
        self.stdout.write("Domain updated successfully.")
