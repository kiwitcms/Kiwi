# -*- coding: utf-8 -*-

import unittest

from tcms.testruns.models import TestRun


class TestTestRun(unittest.TestCase):

    test_fields = (
        'run_id',
        'errata_id',
        'plan_text_version',
        'start_date',
        'stop_date',
        'summary',
        'notes',
        'estimated_time',
        'environment_id',
        'auto_update_run_status',

        'plan', 'plan_id',
        'build', 'build_id',
        'manager', 'manager_id',
        'default_tester', 'default_tester_id',
        'product_version', 'product_version_id',

        'env_value', 'tag', 'cc',
    )

    def setUp(self):
        self.testrun_pks = (43718, 43717)

    def test_to_xmlrpc(self):
        testrun1 = TestRun.objects.get(pk=self.testrun_pks[0])

        result = TestRun.to_xmlrpc(query={'pk__in': self.testrun_pks})
        self.assertEqual(len(result), 2)

        # Verify fields
        sample_testrun = result[0]
        sample_fields = set([name for name in sample_testrun.keys()])
        test_fields = set(self.test_fields)
        test_result = list(sample_fields ^ test_fields)
        self.assertEqual(test_result, [])

        result = dict([(item['run_id'], item) for item in result])

        sample_testrun1 = result[self.testrun_pks[0]]

        self.assertEqual(testrun1.errata_id, sample_testrun1['errata_id'])
        self.assertEqual(testrun1.product_version.pk,
                         sample_testrun1['product_version_id'])
        self.assertEqual(testrun1.product_version.value,
                         sample_testrun1['product_version'])
        self.assertEqual(testrun1.default_tester.pk,
                         sample_testrun1['default_tester_id'])
        self.assertEqual(testrun1.default_tester.username,
                         sample_testrun1['default_tester'])

        tags = [tag.pk for tag in testrun1.tag.all()]
        tags.sort()
        sample_tags = sample_testrun1['tag']
        sample_tags.sort()
        self.assertEqual(tags, sample_tags)


if __name__ == '__main__':
    unittest.main()
