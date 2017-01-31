GET_CONFIRMED_CASES = '''
SELECT
test_cases.case_id, test_cases.creation_date, test_cases.summary,
test_case_categories.name as category_name,
priority.value as priority_value, auth_user.username as author_username
FROM test_cases
INNER JOIN test_case_plans ON (test_cases.case_id = test_case_plans.case_id)
INNER JOIN test_case_categories ON (test_cases.category_id = test_case_categories.category_id)
INNER JOIN priority ON (test_cases.priority_id = priority.id)
INNER JOIN auth_user ON (test_cases.author_id = auth_user.id)
WHERE test_case_plans.plan_id = %s AND test_cases.case_status_id = 2
'''
