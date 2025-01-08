# Copyright (c) 2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from base import LoggedInTestCase
from locust import task
from locust.exception import StopUser


class RecordTestExecutionsTestCase(LoggedInTestCase):
    RANGE_SIZE = 100

    @task
    def record_test_executions(self):
        """
        Range size: R
        Number of test results: R^2
        Number of API requests: 10 + 3R + 2R^2 (incl. on_start)
        """
        user = self.json_rpc("User.filter", {})[0]
        self.json_rpc(
            "Classification.create",
            {"name": f"from locust @ {datetime.now().isoformat()}"},
        )
        classification = self.json_rpc("Classification.filter", {})[0]

        product = self.json_rpc(
            "Product.create",
            {
                "name": f"Product created at {datetime.now().isoformat()}",
                "classification": classification["id"],
            },
        )

        version = self.json_rpc(
            "Version.create",
            {
                "product": product["id"],
                "value": f"ver-{datetime.now().isoformat()}",
            },
        )

        test_plan = self.json_rpc(
            "TestPlan.create",
            {
                "name": f"TP: created at {datetime.now().isoformat()}",
                "text": "A script is creating this TP and adds TCs and TRs to it to establish a performance baseline",
                "type": 7,  # Performance
                "product": product["id"],
                "product_version": version["id"],
                "is_active": True,
            },
        )

        priority = self.json_rpc("Priority.filter", {})[0]
        category = self.json_rpc(
            "Category.filter",
            {
                "product": product["id"],
            },
        )[0]
        confirmed_status = self.json_rpc(
            "TestCaseStatus.filter", {"is_confirmed": True}
        )[0]

        pass_status = self.json_rpc("TestExecutionStatus.filter", {"weight__gt": 0})[0]

        # create new build for all of these TRs
        build = self.json_rpc(
            "Build.create",
            {
                "name": f"b.{datetime.now().isoformat()}",
                "description": f"the product build at {datetime.now().isoformat()}",
                "version": version["id"],
            },
        )

        # create TestCase(s)
        test_cases = []
        for _ in range(self.RANGE_SIZE):
            test_case = self.json_rpc(
                "TestCase.create",
                {
                    "summary": f"Case created at {datetime.now().isoformat()}",
                    "product": product["id"],
                    "category": category["id"],
                    "priority": priority["id"],
                    "case_status": confirmed_status["id"],
                },
            )

            test_cases.append(test_case)
            self.json_rpc("TestPlan.add_case", [test_plan["id"], test_case["id"]])

        # create TestRun(s)
        for i in range(self.RANGE_SIZE):
            test_run = self.json_rpc(
                "TestRun.create",
                {
                    "summary": f"TR {i} {datetime.now().isoformat()}",
                    "manager": user["id"],
                    "plan": test_plan["id"],
                    "build": build["id"],
                },
            )
            print(f'TR-{test_run["id"]} created')

            # add cases to TR
            for case in test_cases:
                result = self.json_rpc("TestRun.add_case", [test_run["id"], case["id"]])

                # record the results
                for execution in result:
                    self.json_rpc(
                        "TestExecution.update",
                        [
                            execution["id"],
                            {
                                "status": pass_status["id"],
                            },
                        ],
                    )

        raise StopUser()
