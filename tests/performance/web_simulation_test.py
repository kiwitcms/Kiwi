# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from base import BrowserTestCase
from locust import task
from locust_plugins.users.playwright import pw


class UserActionsTestCase(BrowserTestCase):
    log_external = False
    log_tasks = False

    @task
    @pw
    async def visit_cases_search_page(self, page):
        await self.setup_page(page)

        await page.goto("/cases/search/")
        await page.wait_for_load_state()

        # note: raise StopUser() doesn't work here
