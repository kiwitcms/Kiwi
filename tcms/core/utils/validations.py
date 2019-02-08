# -*- coding: utf-8 -*-

import re

from django.forms import ValidationError

from tcms.testcases.models import BugSystem


__all__ = (
    'validate_bug_id',
)


# todo: scheduled for removal together with validation regexes
# and validateIssueID on the JavaScript side
def validate_bug_id(bug_id, bug_system_id):
    if not isinstance(bug_id, (str, list, tuple)):
        raise ValidationError('Type error of bug_id.')

    if not bug_system_id:
        raise ValidationError('bug_system_id must not be empty.')

    bug_ids = bug_id
    if not isinstance(bug_ids, (list, tuple)):
        bug_ids = (bug_ids,)

    try:
        bug_system = BugSystem.get_by_id(bug_system_id)
    except BugSystem.DoesNotExist:
        raise ValidationError("Bug system with PK %s doesn't exit" % bug_system_id)
    else:
        id_pattern = bug_system.validate_reg_exp
        if not id_pattern:
            return
        reg_exp = re.compile(id_pattern)

        def error_if_not_match(bug_id):
            if not reg_exp.match(bug_id):
                raise ValidationError(
                    'Please input a valid %s id. %s' % (
                        bug_system.name, bug_system.description))

        map(error_if_not_match, bug_ids)
