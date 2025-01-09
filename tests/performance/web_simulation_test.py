# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from base import BrowserTestCase
from locust import task
from locust.exception import StopUser
from locust_plugins.users.playwright import pw


class UserActionsTestCase(BrowserTestCase):
    @task
    @pw
    async def visit_cases_search_page(self, page):
        await page.context.add_cookies([self.session_cookie])

        await page.goto("/cases/search/")
        await page.wait_for_load_state()

        html = await page.content()
        print(html)
