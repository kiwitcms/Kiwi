TC_PRINTABLE_CASE_TEXTS = '''
SELECT t1.case_id,
       t1.summary,
       t2.setup,
       t2.action,
       t2.effect,
       t2.breakdown
FROM   test_cases t1
       INNER JOIN test_case_texts t2
               ON ( t1.case_id = t2.case_id )
       INNER JOIN (SELECT t4.case_id,
                          Max(t4.case_text_version) AS max_version
                   FROM   test_case_texts t4
                   WHERE  t4.case_id IN ( %s )
                   GROUP  BY t4.case_id) t3
               ON ( t2.case_id = t3.case_id
                    AND t2.case_text_version = t3.max_version )
WHERE  t2.case_id IN ( %s )
'''

TC_EXPORT_ALL_CASES_META = '''
SELECT test_cases.case_id,
       test_cases.summary,
       test_cases.isautomated,
       test_cases.notes,
       priority.value AS priority,
       test_case_status.name AS case_status,
       author.email AS auther_email,
       tester.email AS tester_email,
       test_case_categories.name AS category_name
FROM test_cases
INNER JOIN test_case_status ON (test_cases.case_status_id = test_case_status.case_status_id)
INNER JOIN priority ON (priority.id = test_cases.priority_id)
LEFT JOIN auth_user AS author ON (author.id = test_cases.author_id)
LEFT JOIN auth_user AS tester ON (tester.id = test_cases.default_tester_id)
LEFT JOIN test_case_categories ON (test_case_categories.category_id =
test_cases.category_id)
WHERE (test_cases.case_id IN (%s)
       AND test_case_status.case_status_id IN (1,2,4));
'''
