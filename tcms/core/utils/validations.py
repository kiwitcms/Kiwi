# -*- coding: utf-8 -*-

import re

from tcms.core.exceptions import InvalidBugIdException
from tcms.core.exceptions import InvalidBugSystemException
from tcms.testcases.models import TestCaseBugSystem


__all__ = (
    'validate_bug_id',
)


def validate_bug_id(bug_id, bug_system_id):
    if not isinstance(bug_id, (str, list, tuple)):
        raise TypeError('Type error of bug_id.')

    if not bug_system_id:
        raise InvalidBugIdException('Missing bug system id.')

    bug_ids = bug_id
    if not isinstance(bug_ids, (list, tuple)):
        bug_ids = (bug_ids,)

    try:
        bug_system = TestCaseBugSystem.get_by_id(bug_system_id)
    except TestCaseBugSystem.DoesNotExist:
        raise InvalidBugIdException('Invalid bug system id.')
    else:
        id_pattern = bug_system.validate_reg_exp
        if not id_pattern:
            return None
        reg_exp = re.compile(id_pattern)

        def error_if_not_match(bug_id):
            if not reg_exp.match(bug_id):
                raise InvalidBugSystemException(
                    'Please input a valid %s id. %s' % (
                        bug_system.name, bug_system.description))

        map(error_if_not_match, bug_ids)
