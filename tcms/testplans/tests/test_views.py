# -*- coding: utf-8 -*-

from http import HTTPStatus

from django.urls import reverse

from tcms.tests import BaseCaseRun
from tcms.core.contrib.auth.backends import initiate_user_with_default_setups


class TestAddCasesToRuns(BaseCaseRun):
    """Test adding cases to runs from the TestPlan page"""

    def test_view_loads_fine(self):
        initiate_user_with_default_setups(self.tester)
        self.login_tester()

        url = reverse('plan-choose_run', args=[self.plan.pk])
        response = self.client.get(url, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        # assert basic data is shown
        self.assertContains(response, self.plan.name)
        for test_run in self.plan.run.all():
            self.assertContains(response, test_run.summary)
