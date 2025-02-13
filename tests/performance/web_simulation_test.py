# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import random
from datetime import datetime

import gevent
from base import BrowserTestCase
from locust import between, task
from locust_plugins.users.playwright import pw
from playwright.async_api import expect


class UserActionsTestCase(BrowserTestCase):
    """
    Visit the most commonly visited pages in Kiwi TCMS according to
    curated plausible.io stats. Try to behave like a human with generous
    waiting time between the different pages b/c people don't click at
    lightning fast speed like robots.
    """

    log_external = False
    log_tasks = False
    wait_time = between(60, 300)

    @task(10)
    @pw
    async def clone_test_case(self, page):
        await self.setup_page(page)

        test_cases = self.json_rpc(
            "TestCase.filter",
            {
                "case_status__is_confirmed": True,
            },
        )
        # max 5 test cases at a time b/c it is rare that someone
        # will clone more on a regular basis - plus we add the clones
        # to all possible TestPlans in which the source cases are already included
        how_many = random.randint(1, min(5, len(test_cases)))
        chosen_cases = random.sample(test_cases, how_many)
        target_url = "/cases/clone/?"
        for test_case in chosen_cases:
            target_url += f"c={test_case['id']}&"

        await page.goto(target_url)
        await page.wait_for_load_state()

        # simulate reviewing the selection
        gevent.sleep(random.random() * 60)

        # save
        await page.get_by_text("Close Ad").click()
        await page.get_by_role("button", name="Clone").click()
        await page.wait_for_load_state()

        if len(chosen_cases) > 1:
            success_message = page.locator(".alert-success")
            await expect(success_message).to_contain_text(
                "TestCase cloning was successfull"
            )

    @task(11)
    @pw
    async def visit_test_run_page_and_update_results(self, page):
        await self.setup_page(page)

        # only unfinished TRs
        test_runs = self.json_rpc(
            "TestRun.filter",
            {
                "stop_date__isnull": True,
            },
        )
        chosen_run = random.sample(test_runs, 1)[0]

        await page.goto(f"/runs/{chosen_run['id']}/")
        await page.wait_for_load_state()

        number_of_executions = len(
            self.json_rpc("TestExecution.filter", {"run_id": chosen_run["id"]})
        )
        if number_of_executions > 0:
            executions = self.json_rpc(
                "TestExecution.filter",
                {
                    "run_id": chosen_run["id"],
                },
            )
            how_many = random.randint(1, len(executions))
            chosen_executions = random.sample(executions, how_many)

            # update status with some pause between each
            for execution in chosen_executions:
                row = page.locator(f".test-execution-{execution['id']}")
                await row.click()
                await page.wait_for_load_state()

                now = datetime.now().isoformat()
                await row.locator("div.CodeMirror > div > textarea").fill(
                    f"Recorded by PlayWright at {now}"
                )
                await row.locator("span.status-buttons > i.fa-check-circle-o").click()
                await page.wait_for_load_state()

                gevent.sleep(random.random() * 180)
        else:
            # mark it as finished so we don't select it again
            await page.locator("#stop-button").click()

    @task(15)
    @pw
    async def create_new_test_case(self, page):
        await self.setup_page(page)

        await page.goto("/cases/new/")
        await page.wait_for_load_state()

        now = datetime.now().isoformat()
        await page.locator("#id_summary").fill(f"Test Case by PW at {now}")

        # Simulate typing a long text - up to 2 mins
        gevent.sleep(random.random() * 120)

        await page.locator("div.CodeMirror > div > textarea").fill("Given-When-Then")
        await page.get_by_label("Status").select_option("CONFIRMED")

        # save
        await page.get_by_text("Close Ad").click()
        await page.get_by_role("button", name="Save").click()
        await page.wait_for_url("/case/**/")

    @task(15)
    @pw
    async def create_new_test_run(self, page):
        await self.setup_page(page)

        test_plans = self.json_rpc(
            "TestPlan.filter",
            {},
        )
        chosen_plan = random.sample(test_plans, 1)[0]

        test_cases = self.json_rpc(
            "TestCase.filter",
            {
                "case_status__is_confirmed": True,
                "plan": chosen_plan["id"],
            },
        )

        target_url = f"/runs/from-plan/{chosen_plan['id']}/?"

        if len(test_cases) > 0:
            # will create a TR with max 100 TCs from the chosen TP
            how_many = random.randint(1, min(100, len(test_cases)))
            chosen_cases = random.sample(test_cases, how_many)
            for test_case in chosen_cases:
                target_url += f"c={test_case['id']}&"

        await page.goto(target_url)
        await page.wait_for_load_state()

        await page.get_by_label("Build").select_option("unspecified")
        await page.get_by_role("button", name="Save").click()
        await page.wait_for_url("/runs/**/")
        run_id = await page.locator("#test_run_pk").get_attribute("data-pk")

        h1 = page.locator("h1")
        await expect(h1).to_contain_text("Test run for")

        # chosen TP does not contain any TCs => add TCs to TR!
        if len(test_cases) == 0:
            test_cases = self.json_rpc(
                "TestCase.filter",
                {
                    "case_status__is_confirmed": True,
                },
            )
            how_many = random.randint(1, min(100, len(test_cases)))
            chosen_cases = random.sample(test_cases, how_many)
            for test_case in chosen_cases:
                self.json_rpc("TestRun.add_case", [run_id, test_case["id"]])
                gevent.sleep(random.random() * 5)

    @task(18)
    @pw
    async def create_new_test_plan(self, page):
        await self.setup_page(page)

        await page.goto("/plan/new/")
        await page.wait_for_load_state()

        now = datetime.now().isoformat()
        await page.locator("#id_name").fill(f"Created by PW at {now}")
        await page.locator("div.CodeMirror > div > textarea").fill(
            "This is the body of this TP document"
        )

        # save
        await page.get_by_text("Close Ad").click()
        await page.get_by_role("button", name="Save").click()
        await page.wait_for_url("/plan/**/")
        plan_id = await page.locator("#test_plan_pk").get_attribute("data-testplan-pk")

        # Simulate adding test cases one by one
        gevent.sleep(random.random() * 2.5)

        test_cases = self.json_rpc(
            "TestCase.filter",
            {
                "case_status__is_confirmed": True,
            },
        )
        # max 100 TCs inside a TP
        how_many = random.randint(1, min(100, len(test_cases)))
        chosen_cases = random.sample(test_cases, how_many)
        for test_case in chosen_cases:
            self.json_rpc("TestPlan.add_case", [plan_id, test_case["id"]])
            gevent.sleep(random.random() * 5)

        await page.reload()
        await page.wait_for_load_state()

    @task(20)
    @pw
    async def visit_test_plan_page(self, page):
        await self.setup_page(page)

        test_plans = self.json_rpc(
            "TestPlan.filter",
            {},
        )
        chosen_plan = random.sample(test_plans, 1)[0]

        await page.goto(f"/plan/{chosen_plan['id']}/")
        await page.wait_for_url("/plan/**/**")
        await page.wait_for_load_state()

    @task(21)
    @pw
    async def visit_plans_search_page(self, page):
        await self.setup_page(page)

        await page.goto("/plan/search/")
        await page.wait_for_load_state()

    @task(33)
    @pw
    async def visit_runs_search_page(self, page):
        await self.setup_page(page)

        await page.goto("/runs/search/")
        await page.wait_for_load_state()

    @task(38)
    @pw
    async def visit_cases_search_page(self, page):
        await self.setup_page(page)

        await page.goto("/cases/search/")
        await page.wait_for_load_state()

    @task(100)
    @pw
    async def visit_dashboard_page(self, page):
        await self.setup_page(page)

        await page.goto("/")
        await page.wait_for_load_state()
