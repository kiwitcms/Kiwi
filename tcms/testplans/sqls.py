# -*- coding: utf-8 -*-
TP_EXPORT_ALL_CASES_META = '''
SELECT `test_cases`.`case_id`,
       `test_cases`.`summary`,
       `test_cases`.`isautomated`,
       `test_cases`.`notes`,
       `priority`.`value` AS priority,
       `test_case_status`.`name` AS case_status,
       author.email AS auther_email,
       tester.email AS tester_email,
       `test_case_categories`.`name` AS category_name,
       `test_plans`.`name` AS plan_name,
       `test_plans`.`plan_id`
FROM `test_cases`
INNER JOIN `test_case_status` ON (`test_cases`.`case_status_id` = `test_case_status`.`case_status_id`)
INNER JOIN `test_case_plans` ON (`test_cases`.`case_id` = `test_case_plans`.`case_id`)
INNER JOIN `test_plans` ON (`test_plans`.`plan_id` = `test_case_plans`.`plan_id`)
INNER JOIN `priority` ON (`priority`.`id` = `test_cases`.`priority_id`)
LEFT JOIN `auth_user` AS author ON (author.id = `test_cases`.`author_id`)
LEFT JOIN `auth_user` AS tester ON (tester.id = `test_cases`.`default_tester_id`)
LEFT JOIN `test_case_categories` ON (`test_case_categories`.`category_id` =
`test_cases`.`category_id`)
WHERE (`test_plans`.`plan_id` IN (%s)
       AND `test_case_status`.`case_status_id` IN (1,2,4));
'''

TP_EXPORT_ALL_CASES_COMPONENTS = '''
SELECT `test_case_plans`.`plan_id`,
       `test_case_components`.`case_id`,
       `components`.`id` as component_id,
       `components`.`name` as component_name,
       `products`.`name` as product_name
FROM `components`
INNER JOIN `test_case_components` ON (`components`.`id` = `test_case_components`.`component_id`)
INNER JOIN `products` ON (`products`.`id` = `components`.`product_id`)
INNER JOIN `test_case_plans` ON (`test_case_components`.`case_id` = `test_case_plans`.`case_id`)
WHERE `test_case_plans`.`plan_id` IN (%s)
'''

TP_EXPORT_ALL_CASE_TAGS = '''
SELECT test_case_plans.plan_id,
       test_case_plans.case_id,
       test_tags.tag_name
FROM test_tags
INNER JOIN test_case_tags ON (test_tags.tag_id = test_case_tags.tag_id)
INNER JOIN test_cases ON (test_case_tags.case_id = test_cases.case_id)
INNER JOIN test_case_plans ON (test_cases.case_id = test_case_plans.case_id)
WHERE test_case_plans.plan_id IN (%s)
'''

TP_EXPORT_ALL_CASE_TEXTS = '''
SELECT t3.plan_id,
       test_cases.case_id,
       test_case_texts.setup,
       test_case_texts.action,
       test_case_texts.effect,
       test_case_texts.breakdown
FROM   test_cases
       INNER JOIN test_case_plans
               ON ( test_case_plans.case_id = test_cases.case_id )
       INNER JOIN test_case_texts
               ON ( test_cases.case_id = test_case_texts.case_id )
       INNER JOIN (SELECT t5.plan_id,
                          t4.case_id,
                          Max(t4.case_text_version) AS max_version
                   FROM   test_case_texts t4
                          INNER JOIN test_case_plans t5
                                  ON ( t5.case_id = t4.case_id )
                          INNER JOIN test_cases t6
                                  ON ( t5.case_id = t6.case_id )
                   WHERE  t5.plan_id IN (%s)
                          AND t6.case_status_id IN (1,2,4)
                   GROUP  BY t4.case_id, t5.plan_id) t3
               ON ( test_case_texts.case_id = t3.case_id
                    AND test_case_texts.case_text_version = t3.max_version
                    AND test_case_plans.plan_id = t3.plan_id )
WHERE test_case_plans.plan_id IN (%s)
'''
