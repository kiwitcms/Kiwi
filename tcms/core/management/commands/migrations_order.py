# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import sys

from django.core.management.base import OutputWrapper, no_translations
from django.core.management.commands import migrate


class KiwiOutputWrapper(OutputWrapper):
    def __init__(self, *args, migrate_heading=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.migrate_heading = migrate_heading

    def write(self, msg="", style_func=None, ending=None):
        if style_func == self.migrate_heading:
            super().write(msg)


class Command(migrate.Command):
    """
    Uses migrate --plan to avoid duplicating the internals.
    """

    help = "List the order in which migrations will be applied. Useful for testing & rollback!"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(
            stdout=stdout, stderr=stderr, no_color=no_color, force_color=force_color
        )
        self.stdout = KiwiOutputWrapper(
            stdout or sys.stdout, migrate_heading=self.style.MIGRATE_HEADING
        )

    @no_translations
    def handle(self, *args, **options):
        super().handle(
            app_label=None,
            database="default",
            interactive=False,
            plan=True,
            run_syncdb=False,
            verbosity=1,
            skip_checks=True,
            check_unapplied=False,
        )
