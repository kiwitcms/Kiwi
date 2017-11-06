# -*- coding: utf-8 -*-
class RawSQL:
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

    # Following SQL use for test case run
    completed_case_run_percent = 'SELECT ROUND(no_idle_count/total_count*100,0) \
        FROM ( \
            SELECT \
                tr1.run_id AS run_id, \
                count(tcr1.case_run_id) AS no_idle_count \
            FROM test_runs tr1 \
            LEFT JOIN test_case_runs tcr1 \
            ON tr1.run_id=tcr1.run_id \
            WHERE tcr1.case_run_status_id \
            NOT IN(1,4,5,6) \
            GROUP BY tr1.run_id \
            ORDER BY tr1.run_id \
        ) AS table1, ( \
            SELECT \
                tr2.run_id AS run_id, \
                count(tcr2.case_run_id) AS total_count \
            FROM test_runs tr2 \
            LEFT JOIN test_case_runs tcr2 \
            ON tr2.run_id=tcr2.run_id \
            GROUP BY tr2.run_id \
            ORDER BY tr2.run_id \
        ) AS table2 \
        WHERE table1.run_id=table2.run_id \
        AND table1.run_id=test_runs.run_id'

    total_num_caseruns = 'SELECT COUNT(*) \
        FROM test_case_runs \
        WHERE test_case_runs.run_id = test_runs.run_id'

    failed_case_run_percent = 'SELECT ROUND(no_idle_count/total_count*100,0) \
        FROM (\
            SELECT \
                tr1.run_id AS run_id, \
                count(tcr1.case_run_id) AS no_idle_count \
            FROM test_runs tr1 \
            LEFT JOIN test_case_runs tcr1 \
            ON tr1.run_id=tcr1.run_id \
            WHERE tcr1.case_run_status_id = 3 \
            GROUP BY tr1.run_id ORDER BY tr1.run_id\
        ) AS table1,( \
            SELECT \
                tr2.run_id AS run_id, \
                count(tcr2.case_run_id) AS total_count \
            FROM test_runs tr2 \
            LEFT JOIN test_case_runs tcr2 \
            ON tr2.run_id=tcr2.run_id \
            GROUP BY tr2.run_id \
            ORDER BY tr2.run_id\
        ) AS table2 \
        WHERE table1.run_id=table2.run_id \
        AND table1.run_id=test_runs.run_id'

    passed_case_run_percent = 'SELECT ROUND(no_idle_count/total_count*100,0) \
        FROM (\
            SELECT \
                tr1.run_id AS run_id, \
                count(tcr1.case_run_id) AS no_idle_count \
            FROM test_runs tr1 \
            LEFT JOIN test_case_runs tcr1 \
            ON tr1.run_id=tcr1.run_id \
            WHERE tcr1.case_run_status_id = 2\
            GROUP BY tr1.run_id ORDER BY tr1.run_id\
        ) AS table1,( \
            SELECT \
                tr2.run_id AS run_id, \
                count(tcr2.case_run_id) AS total_count \
            FROM test_runs tr2 \
            LEFT JOIN test_case_runs tcr2 \
            ON tr2.run_id=tcr2.run_id \
            GROUP BY tr2.run_id \
            ORDER BY tr2.run_id\
        ) AS table2 \
        WHERE table1.run_id=table2.run_id \
        AND table1.run_id=test_runs.run_id'

    total_num_review_cases = 'SELECT COUNT(*) FROM tcms_review_cases \
        WHERE tcms_reviews.id = tcms_review_cases.review_id'


class ReportSQL(object):
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
