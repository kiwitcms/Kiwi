# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from locust import FastHttpUser, between, task
from locust_plugins.users.playwright import PlaywrightUser
from requests.utils import dict_from_cookiejar


class LoggedInTestCase(FastHttpUser):
    abstract = True

    username = "testadmin"
    password = "password"
    login_url = "/accounts/login/"

    def on_start(self):
        self.do_login()

    def do_login(self):
        with self.client.get(self.login_url, catch_response=True):
            cookies = dict_from_cookiejar(self.client.cookiejar)
            csrf_middleware_token = cookies["csrftoken"]

            self.client.post(
                self.login_url,
                data={
                    "username": self.username,
                    "password": self.password,
                    "csrfmiddlewaretoken": csrf_middleware_token,
                },
                headers={"Referer": self.host},
            )

    def json_rpc(self, rpc_method, rpc_args):
        # .filter() args are passed as dictionary but other args,
        # e.g. for .add_tag() are passed as a list of positional values
        if not isinstance(rpc_args, list):
            rpc_args = [rpc_args]

        payload = {
            "jsonrpc": "2.0",
            "method": rpc_method,
            "params": rpc_args,
            "id": "jsonrpc",
        }
        return self.client.post("/json-rpc/", json=payload).json()["result"]


class BrowserTestCase(PlaywrightUser, LoggedInTestCase):
    """
    Required setup:
        pip uninstall trio
        playwright install firefox
    """

    abstract = True
    browser_type = "firefox"
    multiplier = 10
    wait_time = between(1, 5)
    session_cookie = None

    def do_login(self):
        pass

    async def _pwprep(self):
        await super()._pwprep()

        # login via the browser
        browser_context = await self.browser.new_context(
            ignore_https_errors=True, base_url=self.host
        )
        page = await browser_context.new_page()
        page.set_default_timeout(60000)

        await page.goto(self.login_url)
        await page.wait_for_load_state()

        await page.locator("#inputUsername").fill(self.username)
        await page.locator("#inputPassword").fill(self.password)
        await page.get_by_role("button").click()

        # store this for later use b/c @pw creates
        # a new context & page for every task!
        for cookie in await page.context.cookies():
            if cookie["name"] == "sessionid":
                self.session_cookie = cookie

        await page.close()
        await browser_context.close()


class ExampleTestCase(LoggedInTestCase):
    wait_time = between(1, 5)

    @task
    def rpc_user_filter(self):
        self.json_rpc("User.filter", {})

    @task
    def visit_dashboard_page(self):
        self.client.get("/")
