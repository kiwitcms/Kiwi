# -*- coding: utf-8 -*-
class RawSQL:  # pylint: disable=too-few-public-methods
    """
    Record the Raw SQL for operate the database directly.
    """
    # Following SQL use for count case and run in plan
    num_cases = 'SELECT COUNT(*) \
        FROM test_case_plans \
        WHERE test_case_plans.plan_id = test_plans.plan_id'

    num_runs = 'SELECT COUNT(*) \
        FROM test_runs \
        WHERE test_runs.plan_id = test_plans.plan_id'

    num_plans = 'SELECT COUNT(*) \
        FROM test_plans AS ch_plans\
        WHERE ch_plans.parent_id = test_plans.plan_id'

    num_case_bugs = 'SELECT COUNT(*) \
        FROM test_case_bugs \
        WHERE test_case_bugs.case_id = test_cases.case_id'

    num_case_run_bugs = 'SELECT COUNT(*) \
        FROM test_case_bugs \
        WHERE test_case_bugs.case_run_id = test_case_runs.case_run_id'


class ReportSQL(object):  # pylint: disable=too-few-public-methods
    # Index
    index_product_plans_count = 'SELECT COUNT(plan_id) \
        FROM test_plans \
        WHERE test_plans.product_id = products.id'

    index_product_runs_count = 'SELECT COUNT(run_id) \
        FROM test_runs \
        INNER JOIN test_plans \
        ON test_runs.plan_id = test_plans.plan_id \
        WHERE test_plans.product_id = products.id'

    index_product_cases_count = 'SELECT COUNT(case_id) \
        FROM test_case_plans \
        INNER JOIN test_plans \
        ON test_case_plans.plan_id = test_plans.plan_id \
        WHERE test_plans.product_id = products.id'

    # Custom Search Zone
    # added by chaobin
    case_runs_count_by_status_under_run = 'SELECT COUNT(DISTINCT case_run_id) \
        FROM test_case_runs \
        WHERE test_case_runs.run_id = test_runs.run_id AND test_case_runs.case_run_status_id = %s'

    custom_details_case_run_count = 'SELECT tcrs.name \
        AS test_case_status, COUNT(tcr.case_id) AS case_run_count \
        FROM test_case_run_status tcrs          \
        LEFT JOIN test_case_runs tcr ON tcrs.case_run_status_id = tcr.case_run_status_id \
        WHERE tcr.run_id = %s \
        GROUP BY tcrs.name \
        ORDER BY tcrs.sortkey'
