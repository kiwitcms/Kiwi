# -*- coding: utf-8 -*-
class RawSQL:  # pylint: disable=too-few-public-methods
    """
    Record the Raw SQL for operate the database directly.
    """
    # Following SQL use for count case and run in plan
    num_cases = 'SELECT COUNT(*) \
        FROM testcases_testcaseplan \
        WHERE testcases_testcaseplan.plan_id = testplans_testplan.plan_id'

    num_runs = 'SELECT COUNT(*) \
        FROM testruns_testrun \
        WHERE testruns_testrun.plan_id = testplans_testplan.plan_id'

    num_plans = 'SELECT COUNT(*) \
        FROM testplans_testplan AS ch_plans\
        WHERE ch_plans.parent_id = testplans_testplan.plan_id'

    num_case_bugs = 'SELECT COUNT(*) \
        FROM testcases_bug \
        WHERE testcases_bug.case_id = testcases_testcase.case_id'

    num_case_run_bugs = 'SELECT COUNT(*) \
        FROM testcases_bug \
        WHERE testcases_bug.case_run_id = testruns_testcaserun.case_run_id'


class ReportSQL(object):  # pylint: disable=too-few-public-methods
    # Index
    index_product_plans_count = 'SELECT COUNT(plan_id) \
        FROM testplans_testplan \
        WHERE testplans_testplan.product_id = management_product.id'

    index_product_runs_count = 'SELECT COUNT(run_id) \
        FROM testruns_testrun \
        INNER JOIN testplans_testplan \
        ON testruns_testrun.plan_id = testplans_testplan.plan_id \
        WHERE testplans_testplan.product_id = management_product.id'

    index_product_cases_count = 'SELECT COUNT(case_id) \
        FROM testcases_testcaseplan \
        INNER JOIN testplans_testplan \
        ON testcases_testcaseplan.plan_id = testplans_testplan.plan_id \
        WHERE testplans_testplan.product_id = management_product.id'

    # Custom Search Zone
    # added by chaobin
    case_runs_count_by_status_under_run = 'SELECT COUNT(DISTINCT case_run_id) \
        FROM testruns_testcaserun \
        WHERE testruns_testcaserun.run_id = testruns_testrun.run_id AND testruns_testcaserun.case_run_status_id = %s'

    custom_details_case_run_count = 'SELECT tcrs.name \
        AS testcases_testcasestatus, COUNT(tcr.case_id) AS case_run_count \
        FROM testruns_testcaserunstatus tcrs          \
        LEFT JOIN testruns_testcaserun tcr ON tcrs.case_run_status_id = tcr.case_run_status_id \
        WHERE tcr.run_id = %s \
        GROUP BY tcrs.name \
        ORDER BY tcrs.sortkey'
