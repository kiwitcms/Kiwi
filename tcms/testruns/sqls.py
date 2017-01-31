GET_CONFIRMED_CASES = '''
SELECT
`test_cases`.`case_id`, `test_cases`.`creation_date`, `test_cases`.`summary`,
`test_case_categories`.`name` as category_name,
`priority`.`value` as priority_value, `auth_user`.`username` as author_username
FROM `test_cases`
INNER JOIN `test_case_plans` ON (`test_cases`.`case_id` = `test_case_plans`.`case_id`)
INNER JOIN `test_case_categories` ON (`test_cases`.`category_id` = `test_case_categories`.`category_id`)
INNER JOIN `priority` ON (`test_cases`.`priority_id` = `priority`.`id`)
INNER JOIN `auth_user` ON (`test_cases`.`author_id` = `auth_user`.`id`)
WHERE `test_case_plans`.`plan_id` = %s AND `test_cases`.`case_status_id` = 2
'''

GET_RUN_BUG_IDS = '''
SELECT test_case_bugs.bug_id, test_case_bug_systems.url_reg_exp
FROM test_case_bugs
INNER JOIN test_case_runs ON (test_case_bugs.case_run_id = test_case_runs.case_run_id)
INNER JOIN test_case_bug_systems ON (test_case_bugs.bug_system_id = test_case_bug_systems.id)
WHERE test_case_runs.run_id = %s
'''

GET_CASERUNS_BUGS = '''
SELECT test_case_runs.case_run_id,
    test_case_bugs.bug_id,
    test_case_bug_systems.url_reg_exp
FROM test_case_runs
INNER JOIN test_case_bugs
    ON (test_case_runs.case_run_id = test_case_bugs.case_run_id)
INNER JOIN test_case_bug_systems
    ON (test_case_bugs.bug_system_id = test_case_bug_systems.id)
WHERE test_case_runs.run_id = %s
ORDER BY test_case_runs.case_run_id
'''

GET_CASERUNS_COMMENTS = '''
select test_case_runs.case_run_id, auth_user.username,
    django_comments.submit_date, django_comments.comment
from test_case_runs
inner join django_comments
    on (test_case_runs.case_run_id = django_comments.object_pk)
inner join auth_user on (django_comments.user_id = auth_user.id)
where django_comments.site_id = %s and
    django_comments.content_type_id = %s and
    django_comments.is_public = 1 and
    django_comments.is_removed = 0 and
    test_case_runs.run_id = %s
ORDER BY test_case_runs.case_run_id
'''
