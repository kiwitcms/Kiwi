import os
import random

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

import tcms_api

from tcms.tests.factories import UserFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import VersionFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests.factories import TestCaseCategoryFactory

from tcms.core.contrib.auth.backends import initiate_user_with_default_setups


class BaseAPIClient_TestCase(StaticLiveServerTestCase):
    """
        Bring up a local Django instance and
        prepare test data - create Test Cases, Test Plans and Test Runs
    """

    # reload data which came from migrations like standard
    # groups Admin and Tester
    serialized_rollback = True

    # how many test objects to create
    num_cases = 1
    num_plans = 1
    num_runs = 1

    def setUp(self):
        # disable caching for every test to avoid hard to debug issues
        # tests that need caching will enable it before they do
        # anything else
        tcms_api.config.set_cache_level(tcms_api.config.CACHE_NONE)

    # NOTE: we setup the required DB data and API objects here
    # because this method is executed *AFTER* setUpClass() and the
    # serialized rollback is not yet available during setUpClass()
    # execution
    def _fixture_setup(self):
        # restore the serialized data from initial migrations
        # this includes default groups and permissions
        super(BaseAPIClient_TestCase, self)._fixture_setup()

        # initial cache reset to avoid storing anything in cache
        tcms_api.config.set_cache_level(tcms_api.config.CACHE_NONE)

        # reset connection to server b/c the address changes for
        # every test and the client caches this as a class attribute
        tcms_api.Nitrate._connection = None
        # also the config is a singleton so reset that too
        # to force config reload
        tcms_api.Config._instance = None

        # API user
        self.api_user, _ = User.objects.get_or_create(
            username='api-tester',
            email='api@example.com')
        self.api_user.set_password('testing')
        initiate_user_with_default_setups(self.api_user)

        # WARNING: for now we override the config file
        # until we can pass the testing configuration
        # TODO: change config values instead of overwriting files on disk
        conf_path = os.path.expanduser('~/.tcms.conf')
        conf_fh = open(conf_path, 'w')
        conf_fh.write("""[nitrate]
url = %s/xmlrpc/
username = %s
password = %s
""" % (self.live_server_url, self.api_user.username, 'testing'))
        conf_fh.close()

        # create the product first so we can fetch it via API
        f_product = ProductFactory()
        self.product = tcms_api.Product(name=f_product.name)
        f_version = VersionFactory(product=f_product)
        self.version = tcms_api.Version(product=self.product, version=f_version.value)
        self.plantype = tcms_api.PlanType(name="Function")

        f_category = TestCaseCategoryFactory(product=f_product)
        self.category = tcms_api.Category(category=f_category.name, product=self.product)

        self.component = tcms_api.Component(name='tcms_api', product=self.product)
        self.CASESTATUS = tcms_api.CaseStatus("CONFIRMED")
        self.build = tcms_api.Build(product=self.product, build="unspecified")

        f_tags = [TestTagFactory() for i in range(20)]
        self.tags = [tcms_api.Tag(t.pk) for t in f_tags]

        f_users = [UserFactory() for i in range(50)]
        self.TESTERS = [tcms_api.User(u.pk) for u in f_users]

        # Create test cases
        self.cases = []
        for case_count in range(self.num_cases):
            testcase = tcms_api.TestCase(
                category=self.category,
                product=self.product,
                summary="Test Case {0}".format(case_count + 1),
                status=self.CASESTATUS)
            # Add a couple of random tags and the default tester
            testcase.tags.add([random.choice(self.tags) for counter in range(10)])
            testcase.tester = random.choice(self.TESTERS)
            testcase.update()
            self.cases.append(testcase)

        # Create master test plan (parent of all)
        self.master = tcms_api.TestPlan(
            name="API client Test Plan",
            document='plan creted from API',
            product=self.product,
            version=self.version,
            type=self.plantype)
        tcms_api.info("* {0}".format(self.master))
        self.master.testcases.add(self.cases)
        self.master.update()

        # Create child test plans
        self.testruns = []
        for plan_count in range(self.num_plans):
            testplan = tcms_api.TestPlan(
                name="Test Plan {0}".format(plan_count + 1),
                document='plan creted from API',
                product=self.product,
                version=self.version,
                parent=self.master,
                type=self.plantype)
            # Link all test cases to the test plan
            testplan.testcases.add(self.cases)
            testplan.update()
            tcms_api.info("  * {0}".format(testplan))

            # Create test runs
            for run_count in range(self.num_runs):
                testrun = tcms_api.TestRun(
                    testplan=testplan,
                    build=self.build,
                    product=self.product,
                    summary="Test Run {0}".format(run_count + 1),
                    version=self.version.name)
                tcms_api.info("    * {0}".format(testrun))
                self.testruns.append(testrun)
