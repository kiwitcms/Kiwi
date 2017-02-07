# -*- coding: utf-8 -*-
from collections import namedtuple


SQLStatement = namedtuple('SQLStatement',
                          'sql_template, default_joins, default_where')


build_builds_total_runs_count = '''
SELECT test_runs.build_id, COUNT(*) AS total_count
FROM test_runs
INNER JOIN test_builds ON (test_runs.build_id = test_builds.build_id)
WHERE test_builds.product_id = %s
GROUP BY test_runs.build_id'''

build_builds_finished_runs_count = '''
SELECT test_runs.build_id, COUNT(*) AS total_count
FROM test_runs
INNER JOIN test_builds ON (test_runs.build_id = test_builds.build_id)
WHERE test_builds.product_id = %s AND test_runs.stop_date IS NOT NULL
GROUP BY test_runs.build_id'''

build_finished_caseruns_count = '''
SELECT tbs.build_id, COUNT(*) AS total_count
FROM test_builds AS tbs
INNER JOIN test_runs AS trs ON (trs.build_id = tbs.build_id)
INNER JOIN test_case_runs AS tcrs ON (tcrs.run_id = trs.run_id)
WHERE tbs.product_id = %s AND tcrs.case_run_status_id NOT IN (1, 4, 5, 6)
GROUP BY tbs.build_id'''

build_failed_caseruns_count = '''
SELECT tbs.build_id, COUNT(*) AS total_count
FROM test_builds AS tbs
INNER JOIN test_runs AS trs ON (trs.build_id = tbs.build_id)
INNER JOIN test_case_runs AS tcrs ON (tcrs.run_id = trs.run_id)
INNER JOIN test_case_run_status AS tcrss ON (tcrs.case_run_status_id = tcrss.case_run_status_id)
WHERE tbs.product_id = %s AND tcrss.name = 'FAILED'
GROUP BY tbs.build_id'''

build_caseruns_count = '''
SELECT tbs.build_id, COUNT(*) AS total_count
FROM test_builds AS tbs
INNER JOIN test_runs AS trs ON (trs.build_id = tbs.build_id)
INNER JOIN test_case_runs AS tcrs ON (tcrs.run_id = trs.run_id)
WHERE tbs.product_id = %s
GROUP BY tbs.build_id'''

build_caserun_status_subtotal = '''
SELECT tcrss.name, COUNT(*) AS total_count
FROM test_case_run_status AS tcrss
INNER JOIN test_case_runs AS tcrs ON (tcrss.case_run_status_id = tcrs.case_run_status_id)
INNER JOIN test_runs AS trs ON (trs.run_id = tcrs.run_id)
INNER JOIN test_builds AS tbs ON (trs.build_id = tbs.build_id)
WHERE tbs.product_id = %s AND tbs.build_id = %s
GROUP BY tcrss.name WITH ROLLUP'''

component_total_cases = '''
SELECT tccs.component_id, COUNT(*) AS total_count
FROM test_case_components AS tccs
INNER JOIN components ON (tccs.component_id = components.id)
WHERE components.product_id = %s
GROUP BY tccs.component_id'''

component_failed_case_runs_count = '''
SELECT tccs.component_id, COUNT(*) AS total_count
FROM test_case_components AS tccs
INNER JOIN components ON (tccs.component_id = components.id)
INNER JOIN test_cases AS tcs ON (tccs.case_id = tcs.case_id)
INNER JOIN test_case_runs AS tcrs ON (tcs.case_id = tcrs.case_id)
WHERE tcrs.case_run_status_id = 3 AND components.product_id = %s
GROUP BY tccs.component_id'''

component_finished_case_runs_count = '''
SELECT tccs.component_id, COUNT(*) AS total_count
FROM test_case_components AS tccs
INNER JOIN components ON (tccs.component_id = components.id)
INNER JOIN test_cases AS tcs ON (tccs.case_id = tcs.case_id)
INNER JOIN test_case_runs AS tcrs ON (tcs.case_id = tcrs.case_id)
WHERE tcrs.case_run_status_id NOT IN (1, 4, 5, 6) and components.product_id = %s
GROUP BY tccs.component_id'''

component_total_case_runs_count = '''
SELECT tccs.component_id, COUNT(*) AS total_count
FROM test_case_components AS tccs
INNER JOIN components ON (tccs.component_id = components.id)
INNER JOIN test_cases AS tcs ON (tccs.case_id = tcs.case_id)
INNER JOIN test_case_runs AS tcrs ON (tcs.case_id = tcrs.case_id)
WHERE components.product_id = %s
GROUP BY tccs.component_id'''

component_case_runs_count = '''
SELECT tcrss.name, COUNT(*) AS total_count
FROM test_case_run_status AS tcrss
INNER JOIN test_case_runs AS tcrs ON (tcrss.case_run_status_id = tcrs.case_run_status_id)
INNER JOIN test_cases AS tcs ON (tcrs.case_id = tcs.case_id)
INNER JOIN test_case_components AS tccs ON (tcs.case_id = tccs.case_id)
WHERE tccs.component_id = %s
GROUP BY tcrss.name WITH ROLLUP'''

version_plans_subtotal = '''
SELECT test_plans.product_version_id, count(*) as total_count
FROM test_plans
WHERE test_plans.product_id = %s
GROUP BY test_plans.product_version_id'''

version_running_runs_subtotal = '''
SELECT test_plans.product_version_id, COUNT(*) as total_count
FROM test_plans
INNER JOIN test_runs ON (test_plans.plan_id = test_runs.plan_id)
WHERE test_plans.product_id = %s AND test_runs.stop_date IS NULL
GROUP BY test_plans.product_version_id'''

version_finished_runs_subtotal = '''
SELECT test_plans.product_version_id, COUNT(*) as total_count
FROM test_plans
INNER JOIN test_runs ON (test_plans.plan_id = test_runs.plan_id)
WHERE test_plans.product_id = %s AND test_runs.stop_date IS NOT NULL
GROUP BY test_plans.product_version_id'''

version_cases_subtotal = '''
SELECT test_plans.product_version_id, COUNT(*) as total_count
FROM test_plans
INNER JOIN test_case_plans ON (test_plans.plan_id = test_case_plans.plan_id)
WHERE test_plans.product_id = %s
GROUP BY test_plans.product_version_id'''

version_case_runs_subtotal = '''
SELECT test_plans.product_version_id, COUNT(*) AS total_count
FROM test_plans
INNER JOIN test_runs ON (test_plans.plan_id = test_runs.plan_id)
INNER JOIN test_case_runs ON (test_runs.run_id = test_case_runs.run_id)
WHERE test_plans.product_id = %s
GROUP BY test_plans.product_version_id'''

version_finished_case_runs_subtotal = '''
SELECT test_plans.product_version_id, COUNT(*) AS total_count
FROM test_plans
INNER JOIN test_runs ON (test_plans.plan_id = test_runs.plan_id)
INNER JOIN test_case_runs ON (test_runs.run_id = test_case_runs.run_id)
WHERE test_plans.product_id = %s AND
    test_case_runs.case_run_status_id NOT IN (1, 4, 5, 6)
GROUP BY test_plans.product_version_id'''

version_failed_case_runs_subtotal = '''
SELECT test_plans.product_version_id, COUNT(*) AS total_count
FROM test_plans
INNER JOIN test_runs ON (test_plans.plan_id = test_runs.plan_id)
INNER JOIN test_case_runs ON (test_runs.run_id = test_case_runs.run_id)
WHERE test_plans.product_id = %s AND test_case_runs.case_run_status_id = 3
GROUP BY test_plans.product_version_id'''

### SQL for custom report ###


custom_builds = SQLStatement(
    sql_template='''
SELECT DISTINCT test_builds.build_id, test_builds.name
FROM test_builds
%(joins)s
WHERE %(where)s''',
    default_joins=(),
    default_where=())

custom_builds_runs_subtotal = SQLStatement(
    sql_template='''
SELECT test_builds.build_id, COUNT(DISTINCT test_runs.run_id) AS total_count
FROM test_builds
%(joins)s
WHERE %(where)s
GROUP BY test_builds.build_id WITH ROLLUP''',
    default_joins=(
        'INNER JOIN test_runs ON (test_builds.build_id = test_runs.build_id)',
    ),
    default_where=())


custom_builds_plans_subtotal = SQLStatement(
    sql_template='''
SELECT test_builds.build_id, COUNT(DISTINCT test_runs.plan_id) AS total_count
FROM test_builds
%(joins)s
WHERE %(where)s
GROUP BY test_builds.build_id WITH ROLLUP''',
    default_joins=(
        'INNER JOIN test_runs ON (test_builds.build_id = test_runs.build_id)',
    ),
    default_where=())


custom_builds_cases_isautomated_subtotal = SQLStatement(
    sql_template='''
SELECT test_cases.isautomated, COUNT(DISTINCT test_cases.case_id) AS total_count
FROM test_builds
%(joins)s
WHERE %(where)s
GROUP BY test_cases.isautomated WITH ROLLUP''',
    default_joins=(
        'INNER JOIN test_runs ON (test_builds.build_id = test_runs.build_id)',
        'INNER JOIN test_case_runs ON (test_runs.run_id = test_case_runs.run_id)',
        'INNER JOIN test_cases ON (test_case_runs.case_id = test_cases.case_id)'
    ),
    default_where=())


# Percentage of passed and failed case runs
custom_builds_case_runs_subtotal_by_status = SQLStatement(
    sql_template='''
SELECT test_builds.build_id, test_case_runs.case_run_status_id,
    COUNT(DISTINCT test_case_runs.case_run_id) AS total_count
FROM test_builds
%(joins)s
WHERE %(where)s
GROUP BY test_builds.build_id, test_case_runs.case_run_status_id''',
    default_joins=(
        'INNER JOIN test_runs ON (test_builds.build_id = test_runs.build_id)',
        'INNER JOIN test_case_runs ON (test_runs.run_id = test_case_runs.run_id)',
    ),
    default_where=(
        'test_case_runs.case_run_status_id IN (2, 3)',))


custom_builds_case_runs_subtotal = SQLStatement(
    sql_template='''
SELECT test_builds.build_id, COUNT(DISTINCT test_case_runs.case_run_id) AS total_count
FROM test_builds
%(joins)s
WHERE %(where)s
GROUP BY test_builds.build_id''',
    default_joins=(
        'INNER JOIN test_runs ON (test_builds.build_id = test_runs.build_id)',
        'INNER JOIN test_case_runs ON (test_runs.run_id = test_case_runs.run_id)',
    ),
    default_where=())


custom_details_status_matrix = '''
SELECT test_plans.plan_id, test_plans.name, test_runs.run_id, test_runs.summary,
    test_case_run_status.name, count(*) as total_count
FROM test_plans
INNER JOIN test_runs on (test_plans.plan_id = test_runs.plan_id)
INNER JOIN test_case_runs on (test_case_runs.run_id = test_runs.run_id)
INNER JOIN test_case_run_status on (test_case_runs.case_run_status_id = test_case_run_status.case_run_status_id)
WHERE test_runs.build_id IN %s
GROUP BY test_plans.plan_id, test_runs.run_id, test_case_runs.case_run_status_id
ORDER BY test_plans.plan_id, test_runs.run_id'''


custom_details_case_runs_comments = '''
SELECT
    test_case_runs.case_run_id,
    django_comments.comment, django_comments.submit_date, auth_user.username
FROM django_comments
INNER JOIN auth_user ON (django_comments.user_id = auth_user.id)
INNER JOIN test_case_runs ON (django_comments.object_pk = test_case_runs.case_run_id)
INNER JOIN test_runs ON (test_runs.run_id = test_case_runs.run_id)
WHERE
    django_comments.content_type_id = %s AND django_comments.site_id = 1 AND
    django_comments.is_removed = 0 AND test_runs.build_id IN %s AND
    test_case_runs.case_run_status_id IN %s'''


#### Testing report #######

testing_report_plans_total = '''
select count(distinct test_plans.plan_id) as total_count
from test_runs
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
inner join test_builds on (test_runs.build_id = test_builds.build_id)
where {0}'''

testing_report_runs_total = '''
SELECT COUNT(*) AS total_count
FROM test_builds
INNER JOIN test_runs ON (test_builds.build_id = test_runs.build_id)
WHERE {0}'''

testing_report_case_runs_total = '''
SELECT COUNT(*) AS total_count
FROM test_builds
INNER JOIN test_runs ON (test_runs.build_id = test_builds.build_id)
INNER JOIN test_case_runs ON (test_case_runs.run_id = test_runs.run_id)
WHERE {0}
'''

testing_report_runs_subtotal = '''
select test_runs.build_id, count(*) as total_count
from test_runs
inner join test_builds on (test_runs.build_id = test_builds.build_id)
where {0}
group by test_runs.build_id with rollup'''

# SQLs for report "By Case-Run Tester"

### Report data group by builds ###

by_case_run_tester_status_matrix_groupby_build = '''
select test_builds.build_id, test_case_runs.tested_by_id, test_case_run_status.name, count(*) as total_count
from test_builds
inner join test_runs on (test_builds.build_id = test_runs.build_id)
inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
inner join test_case_run_status on (test_case_run_status.case_run_status_id = test_case_runs.case_run_status_id)
where {0}
group by test_builds.build_id, test_case_runs.tested_by_id, test_case_run_status.name'''

by_case_run_tester_runs_subtotal_groupby_build = '''
select build_id, tested_by_id, count(*) as total_count
from (
    select test_builds.build_id, test_case_runs.tested_by_id, test_case_runs.run_id
    from test_builds
    inner join test_runs on (test_builds.build_id = test_runs.build_id)
    inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
    where {0}
    group by test_builds.build_id, test_case_runs.tested_by_id, test_case_runs.run_id
) as t1
group by build_id, tested_by_id'''

### Report data WITHOUT selecting builds ###

by_case_run_tester_status_matrix = '''
select test_case_runs.tested_by_id, test_case_run_status.name, count(*) as total_count
from test_builds
inner join test_runs on (test_builds.build_id = test_runs.build_id)
inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
inner join test_case_run_status on (test_case_run_status.case_run_status_id = test_case_runs.case_run_status_id)
where {0}
group by test_case_runs.tested_by_id, test_case_run_status.name'''

by_case_run_tester_runs_subtotal = '''
select tested_by_id, count(*) as total_count
from (
    select test_case_runs.tested_by_id, test_case_runs.run_id
    from test_builds
    inner join test_runs on (test_builds.build_id = test_runs.build_id)
    inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
    where {0}
    group by test_case_runs.tested_by_id, test_case_runs.run_id
) as t1
group by tested_by_id'''

### Report data By Case Priority ###

by_case_priority_subtotal = '''
select
    test_builds.build_id,
    priority.id as priority_id, priority.value as priority_value,
    test_case_run_status.name, count(*) as total_count
from test_builds
inner join test_runs on (test_builds.build_id = test_runs.build_id)
inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
inner join test_cases on (test_case_runs.case_id = test_cases.case_id)
inner join test_case_run_status on (
    test_case_runs.case_run_status_id = test_case_run_status.case_run_status_id)
inner join priority on (test_cases.priority_id = priority.id)
where {0}
group by test_builds.build_id, priority.id, test_case_run_status.name'''

### Report data By Plan Tags ###

by_plan_tags_plans_subtotal = '''
select test_plan_tags.tag_id, count(distinct test_plans.plan_id) as total_count
from test_builds
inner join test_runs on (test_builds.build_id = test_runs.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
left join test_plan_tags on (test_plans.plan_id = test_plan_tags.plan_id)
where {0}
group by test_plan_tags.tag_id'''

by_plan_tags_runs_subtotal = '''
select test_plan_tags.tag_id, count(distinct test_runs.run_id) as total_count
from test_builds
inner join test_runs on (test_builds.build_id = test_runs.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
left join test_plan_tags on (test_plans.plan_id = test_plan_tags.plan_id)
where {0}
group by test_plan_tags.tag_id'''

by_plan_tags_passed_failed_case_runs_subtotal = '''
select test_plan_tags.tag_id, test_case_run_status.name, count(distinct test_case_runs.case_run_id) as total_count
from test_plans
inner join test_runs on (test_plans.plan_id = test_runs.plan_id)
inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
inner join test_case_run_status on (test_case_run_status.case_run_status_id = test_case_runs.case_run_status_id)
inner join test_builds on (test_builds.build_id = test_runs.build_id)
left join test_plan_tags on (test_plans.plan_id = test_plan_tags.plan_id)
where test_case_run_status.name in ('PASSED', 'FAILED') and {0}
group by test_plan_tags.tag_id, test_case_run_status.name'''

### Report data of details of By Plan Tags ###

by_plan_tags_detail_status_matrix = '''
select
    test_plan_tags.tag_id,
    test_builds.build_id, test_builds.name as build_name,
    test_plans.plan_id, test_plans.name as plan_name,
    test_runs.run_id, test_runs.summary,
    test_case_run_status.name as status_name, count(*) as total_count
from test_builds
inner join test_runs on (test_builds.build_id = test_runs.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
inner join test_case_runs on (test_runs.run_id = test_case_runs.run_id)
inner join test_case_run_status on (test_case_runs.case_run_status_id = test_case_run_status.case_run_status_id)
left join test_plan_tags on (test_plans.plan_id = test_plan_tags.plan_id)
where {0}
group by test_plan_tags.tag_id, test_builds.build_id, test_plans.plan_id,
    test_runs.run_id, test_case_run_status.name'''

### Report data of By Plan Build ###

by_plan_build_builds_subtotal = '''
select test_plans.plan_id, test_plans.name, count(distinct test_builds.build_id) as total_count
from test_builds
inner join test_runs on (test_runs.build_id = test_builds.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
where {0}
group by test_runs.plan_id'''

by_plan_build_runs_subtotal = '''
select test_plans.plan_id, test_plans.name, count(distinct test_runs.run_id) as total_count
from test_builds
inner join test_runs on (test_runs.build_id = test_builds.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
where {0}
group by test_runs.plan_id'''

by_plan_build_status_matrix = '''
select
    test_plans.plan_id, test_plans.name,
    test_case_run_status.name,
    count(distinct test_runs.run_id) as total_count
from test_builds
inner join test_runs on (test_runs.build_id = test_builds.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
inner join test_case_runs on (test_case_runs.run_id = test_runs.run_id)
inner join test_case_run_status on (
    test_case_runs.case_run_status_id = test_case_run_status.case_run_status_id)
where test_case_run_status.name in ('PASSED', 'FAILED')  AND {0}
group by test_runs.plan_id, test_case_run_status.name'''

### Report data of By Plan Build detail ###

by_plan_build_detail_status_matrix = '''
select
    test_runs.plan_id, test_plans.name as plan_name,
    test_runs.build_id, test_builds.name as build_name,
    test_runs.run_id, test_runs.summary as run_summary,
    test_case_run_status.name as status_name, count(*) as total_count
from test_builds
inner join test_runs on (test_runs.build_id = test_builds.build_id)
inner join test_plans on (test_runs.plan_id = test_plans.plan_id)
inner join test_case_runs on (test_case_runs.run_id = test_runs.run_id)
inner join test_case_run_status on (
    test_case_runs.case_run_status_id = test_case_run_status.case_run_status_id)
where {0}
group by
    test_runs.plan_id, test_runs.build_id,
    test_runs.run_id, test_case_run_status.name'''
