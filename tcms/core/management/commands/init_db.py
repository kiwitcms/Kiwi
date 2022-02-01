from django.core.management.commands import migrate


class Command(migrate.Command):
    help = "Executes ./manage.py migrate and prints a marker at the end!"

    def handle(self, *args, **kwargs):
        super().handle(*args, **kwargs)
        self.stdout.write("\ninit-db is done")
