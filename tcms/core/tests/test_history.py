# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, no-member

from tcms.tests import BasePlanCase


class RemoveUserWhenThereIsHistory(BasePlanCase):
    def setUp(self):
        self.case.summary = 'editted to generate history'
        self.case.save()
        # map history to a user which we try to delete later
        for history_record in self.case.history.all():
            history_record.history_user = self.tester
            history_record.save()

    def test_remove_user(self):
        self.tester.delete()
        # 2 edits + 1 cascade delete
        self.assertEqual(3, self.case.history.count())

        # when users are removed this is supposed to be set to None
        for history_record in self.case.history.all():
            self.assertIsNone(history_record.history_user)
