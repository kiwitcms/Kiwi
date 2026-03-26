from datetime import timedelta

from django.db.models import F
from django.db.models.functions import Coalesce

from tcms.testruns.models import TestExecution

_TEST_EXECUTION_FIELDS = (
    "id",
    "assignee",
    "tested_by",
    "case_text_version",
    "start_date",
    "stop_date",
    "sortkey",
    "run",
    "case",
    "status",
    "build",
)


class TestExecutionDAO:
    def __init__(self):
        # new storage: maps execution_id (int) -> execution dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, execution):
        """Convert a TestExecution object to a plain dict with public fields."""
        result = {field: getattr(execution, field) for field in _TEST_EXECUTION_FIELDS}
        # store PKs, not related objects
        result["assignee"] = execution.assignee_id
        result["tested_by"] = execution.tested_by_id
        result["run"] = execution.run_id
        result["case"] = execution.case_id
        result["status"] = execution.status_id
        result["build"] = execution.build_id
        result["expected_duration"] = (
            (execution.case.setup_duration or timedelta(0))
            + (execution.case.testing_duration or timedelta(0))
        )
        result["actual_duration"] = execution.actual_duration
        # Fetch related names via DB query to match filter() output exactly (bypasses translation)
        extra = TestExecution.objects.filter(pk=execution.pk).annotate(
            actual_duration=F("stop_date") - F("start_date"),
        ).values(
            "assignee__username", "tested_by__username", "case__summary",
            "build__name", "status__name", "status__icon", "status__color",
            "actual_duration",
        ).first() or {}
        result.update(extra)
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[TestExecutionDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[TestExecutionDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of test execution dicts matching query.
        Used by the TestExecution.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            TestExecution.objects.annotate(
                expected_duration=(
                    Coalesce("case__setup_duration", timedelta(0))
                    + Coalesce("case__testing_duration", timedelta(0))
                ),
                actual_duration=F("stop_date") - F("start_date"),
            )
            .filter(**query)
            .values(
                *_TEST_EXECUTION_FIELDS,
                "assignee__username",
                "tested_by__username",
                "case__summary",
                "build__name",
                "status__name",
                "status__icon",
                "status__color",
                "expected_duration",
                "actual_duration",
            )
            .order_by("id")
            .distinct()
        )

        # NEW storage - only executions previously written through DAO
        new_result = [self._store[e["id"]] for e in old_result if e["id"] in self._store]

        if new_result:
            old_subset = [e for e in old_result if e["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[TestExecutionDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def get_by_id(self, execution_id):
        """
        Return a single TestExecution object by primary key.
        """
        # OLD storage
        old_result = TestExecution.objects.get(pk=execution_id)

        # NEW storage
        new_result = self._store.get(execution_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(
                f"[TestExecutionDAO] get_by_id: execution id={execution_id} not in new storage yet"
                f" - skipping comparison"
            )

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, execution, update_fields=None):
        """
        Persist a TestExecution object.
        Used by TestExecution.create and TestExecution.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            execution.save(update_fields=update_fields)
        else:
            execution.save()

        # NEW storage - store the current state of the execution
        self._store[execution.pk] = self._to_dict(execution)

        print(f"[TestExecutionDAO] save: synced execution id={execution.pk} to new storage")
        return execution

    def remove(self, query):
        """
        Delete TestExecution objects matching query.
        Used by TestExecution.remove RPC endpoint.
        """
        # OLD storage
        deleted = TestExecution.objects.filter(**query).delete()
        print(f"[TestExecutionDAO] remove: deleted {deleted[0]} execution(s)")
        return deleted


test_execution_dao = TestExecutionDAO()
