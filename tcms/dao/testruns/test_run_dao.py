from django.forms.models import model_to_dict

from tcms.testcases.models import TestCase
from tcms.testruns.models import TestExecution, TestRun

_TEST_RUN_FIELDS = (
    "id",
    "start_date",
    "stop_date",
    "planned_start",
    "planned_stop",
    "summary",
    "notes",
    "plan",
    "build",
    "manager",
    "default_tester",
)


class TestRunDAO:
    def __init__(self):
        # new storage: maps run_id (int) -> run dict
        self._store = {}
        # new storage for CC: run_id -> set of user emails
        self._cc = {}
        # new storage for executions: run_id -> list of case PKs added
        self._case_ids = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, run):
        """Convert a TestRun object to a plain dict with public fields."""
        result = {field: getattr(run, field) for field in _TEST_RUN_FIELDS}
        # store PKs, not related objects
        result["plan"] = run.plan_id
        result["build"] = run.build_id
        result["manager"] = run.manager_id
        result["default_tester"] = run.default_tester_id
        # Fetch related names via DB query to match filter() output exactly (bypasses translation)
        extra = TestRun.objects.filter(pk=run.pk).values(
            "plan__name", "build__name", "build__version", "build__version__value",
            "build__version__product", "manager__username", "default_tester__username",
        ).first() or {}
        result.update(extra)
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[TestRunDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[TestRunDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of test run dicts matching query.
        Used by the TestRun.filter RPC endpoint.
        """
        _EXTRA_FIELDS = (
            "plan__name",
            "build__name",
            "build__version",
            "build__version__value",
            "build__version__product",
            "manager__username",
            "default_tester__username",
        )
        # OLD storage
        old_result = list(
            TestRun.objects.filter(**query)
            .values(*_TEST_RUN_FIELDS, *_EXTRA_FIELDS)
            .order_by("id")
            .distinct()
        )

        # NEW storage - only runs previously written through DAO
        new_result = [self._store[r["id"]] for r in old_result if r["id"] in self._store]

        if new_result:
            old_subset = [r for r in old_result if r["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[TestRunDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def filter_objects(self, *args, **kwargs):
        """
        Return a TestRun queryset for use in views and templates.
        """
        return TestRun.objects.filter(*args, **kwargs)

    def get_by_id(self, run_id):
        """
        Return a single TestRun object by primary key.
        """
        # OLD storage
        old_result = TestRun.objects.get(pk=run_id)

        # NEW storage
        new_result = self._store.get(run_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(f"[TestRunDAO] get_by_id: run id={run_id} not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, run, update_fields=None):
        """
        Persist a TestRun object.
        Used by TestRun.create and TestRun.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            run.save(update_fields=update_fields)
        else:
            run.save()

        # NEW storage - store the current state of the run
        self._store[run.pk] = self._to_dict(run)

        print(f"[TestRunDAO] save: synced run id={run.pk} to new storage")
        return run

    def remove(self, query):
        """
        Delete TestRun objects matching query.
        Used by TestRun.remove RPC endpoint.
        """
        # OLD storage
        deleted = TestRun.objects.filter(**query).delete()
        print(f"[TestRunDAO] remove: deleted {deleted[0]} run(s)")
        return deleted

    # ------------------------------------------------------------------
    # TestExecution / add_case / remove_case / get_cases
    # ------------------------------------------------------------------

    @staticmethod
    def _annotate_executions(executions_iterable):
        """Annotate execution objects with their properties."""
        result = []
        for execution in executions_iterable:
            serialized = model_to_dict(execution)
            serialized["properties"] = list(
                execution.properties().values("name", "value")
            )
            result.append(serialized)
        return result

    def add_case(self, run, case):
        """
        Add a TestCase to the given TestRun, creating a TestExecution.
        Used by the TestRun.add_case RPC endpoint.
        """
        # OLD storage
        if run.executions.filter(case=case).exists():
            return self._annotate_executions(run.executions.filter(case=case))

        if not case.case_status.is_confirmed:
            raise RuntimeError(f"TC-{case.pk} status is not confirmed")

        sortkey = 10
        last_te = run.executions.order_by("sortkey").last()
        if last_te:
            sortkey += last_te.sortkey

        result = self._annotate_executions(
            run.create_execution(case=case, sortkey=sortkey)
        )

        # NEW storage — track which cases have been added
        if run.pk not in self._case_ids:
            self._case_ids[run.pk] = set()
        self._case_ids[run.pk].add(case.pk)

        print(f"[TestRunDAO] add_case: added case id={case.pk} to run id={run.pk}")
        return result

    def remove_case(self, run_id, case_id):
        """
        Remove TestExecution(s) for the given case from the given run.
        Used by the TestRun.remove_case RPC endpoint.
        """
        # OLD storage
        TestExecution.objects.filter(run=run_id, case=case_id).delete()

        # NEW storage
        if run_id in self._case_ids:
            self._case_ids[run_id].discard(case_id)

        print(f"[TestRunDAO] remove_case: removed case id={case_id} from run id={run_id}")

    def get_cases(self, run_id):
        """
        Return test cases attached to the given run, augmented with execution info.
        Used by the TestRun.get_cases RPC endpoint.
        """
        # OLD storage
        result = list(
            TestCase.objects.filter(executions__run_id=run_id).values(
                "id",
                "create_date",
                "is_automated",
                "script",
                "arguments",
                "extra_link",
                "summary",
                "requirement",
                "notes",
                "text",
                "case_status",
                "category",
                "priority",
                "author",
                "default_tester",
                "reviewer",
            )
        )

        executions = TestExecution.objects.filter(run_id=run_id).values(
            "case", "pk", "status__name"
        )
        extra_info = {row["case"]: row for row in executions.iterator()}
        for case in result:
            info = extra_info[case["id"]]
            case["execution_id"] = info["pk"]
            case["status"] = info["status__name"]

        # NEW storage — compare tracked case IDs vs what's in DB
        new_case_ids = self._case_ids.get(run_id)
        if new_case_ids is not None:
            old_case_ids = {c["id"] for c in result}
            if not new_case_ids.issubset(old_case_ids):
                print(f"[TestRunDAO] MISMATCH in 'get_cases' for run id={run_id}:")
                print(f"  NEW ids not in OLD: {new_case_ids - old_case_ids}")
            else:
                print(f"[TestRunDAO] OK 'get_cases' for run id={run_id}: all new storage cases present")
        else:
            print(f"[TestRunDAO] get_cases: run id={run_id} not in new storage yet - skipping comparison")

        return result

    # ------------------------------------------------------------------
    # CC operations
    # ------------------------------------------------------------------

    def add_cc(self, run, user):
        """
        Add user to test run CC list.
        Used by the TestRun.add_cc RPC endpoint.
        """
        # OLD storage
        run.add_cc(user)

        # NEW storage
        if run.pk not in self._cc:
            self._cc[run.pk] = set()
        self._cc[run.pk].add(user.email)

        print(f"[TestRunDAO] add_cc: added {user.email} to run id={run.pk}")

    def remove_cc(self, run, user):
        """
        Remove user from test run CC list.
        Used by the TestRun.remove_cc RPC endpoint.
        """
        # OLD storage
        run.remove_cc(user)

        # NEW storage
        if run.pk in self._cc:
            self._cc[run.pk].discard(user.email)

        print(f"[TestRunDAO] remove_cc: removed {user.email} from run id={run.pk}")

    def get_cc(self, run):
        """
        Return CC email list for the given test run.
        Used by the TestRun.get_cc RPC endpoint.
        """
        # OLD storage
        old_result = list(run.cc.values_list("email", flat=True))

        # NEW storage
        new_result = self._cc.get(run.pk)
        if new_result is not None:
            self._compare(set(old_result), new_result, "get_cc")
        else:
            print(f"[TestRunDAO] get_cc: run id={run.pk} not in new storage yet - skipping comparison")

        return old_result


test_run_dao = TestRunDAO()
