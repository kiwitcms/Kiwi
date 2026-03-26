from django.db.models import Count
from django.forms.models import model_to_dict

from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testplans.models import TestPlan

_TEST_PLAN_FIELDS = (
    "id",
    "name",
    "text",
    "create_date",
    "is_active",
    "extra_link",
    "product_version",
    "product",
    "author",
    "type",
    "parent",
)


class TestPlanDAO:
    def __init__(self):
        # new storage: maps plan_id (int) -> plan dict
        self._store = {}
        # new storage for plan-case links: plan_id -> {case_id -> sortkey}
        self._plan_cases = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, plan):
        """Convert a TestPlan object to a plain dict with public fields."""
        result = {field: getattr(plan, field) for field in _TEST_PLAN_FIELDS}
        # store PKs, not related objects
        result["product_version"] = plan.product_version_id
        result["product"] = plan.product_id
        result["author"] = plan.author_id
        result["type"] = plan.type_id
        result["parent"] = plan.parent_id
        # Fetch related names via DB query to match filter() output exactly (bypasses translation)
        extra = TestPlan.objects.filter(pk=plan.pk).annotate(Count("children")).values(
            "product_version__value", "product__name", "author__username", "type__name", "children__count",
        ).first() or {}
        result.update(extra)
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[TestPlanDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[TestPlanDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of test plan dicts matching query.
        Used by the TestPlan.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            TestPlan.objects.filter(**query)
            .values(
                *_TEST_PLAN_FIELDS,
                "product_version__value",
                "product__name",
                "author__username",
                "type__name",
            )
            .annotate(Count("children"))
            .order_by("product", "id")
            .distinct()
        )

        # NEW storage - only plans previously written through DAO
        new_result = [self._store[p["id"]] for p in old_result if p["id"] in self._store]

        if new_result:
            old_subset = [p for p in old_result if p["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[TestPlanDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def filter_objects(self, **kwargs):
        """
        Return a TestPlan queryset for use in views and templates.
        """
        return TestPlan.objects.filter(**kwargs)

    def get_by_id(self, plan_id):
        """
        Return a single TestPlan object by primary key.
        """
        # OLD storage
        old_result = TestPlan.objects.get(pk=plan_id)

        # NEW storage
        new_result = self._store.get(plan_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(f"[TestPlanDAO] get_by_id: plan id={plan_id} not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, plan, update_fields=None):
        """
        Persist a TestPlan object.
        Used by TestPlan.create and TestPlan.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            plan.save(update_fields=update_fields)
        else:
            plan.save()

        # NEW storage - store the current state of the plan
        self._store[plan.pk] = self._to_dict(plan)

        print(f"[TestPlanDAO] save: synced plan id={plan.pk} to new storage")
        return plan

    def add_case(self, plan, case):
        """
        Link a test case to the given test plan.
        Used by the TestPlan.add_case RPC endpoint.
        """
        # OLD storage
        test_case_plan = plan.add_case(case)

        # NEW storage
        if plan.pk not in self._plan_cases:
            self._plan_cases[plan.pk] = {}
        self._plan_cases[plan.pk][case.pk] = test_case_plan.sortkey

        print(f"[TestPlanDAO] add_case: linked case id={case.pk} to plan id={plan.pk}")

        result = model_to_dict(case, exclude=["component", "plan", "tag"])
        result["create_date"] = case.create_date
        result["sortkey"] = test_case_plan.sortkey
        return result

    def remove_case(self, plan_id, case_id):
        """
        Unlink a test case from the given test plan.
        Used by the TestPlan.remove_case RPC endpoint.
        """
        # OLD storage
        TestCasePlan.objects.filter(case=case_id, plan=plan_id).delete()

        # NEW storage
        if plan_id in self._plan_cases:
            self._plan_cases[plan_id].pop(case_id, None)

        print(f"[TestPlanDAO] remove_case: unlinked case id={case_id} from plan id={plan_id}")

    def update_case_order(self, plan_id, case_id, sortkey):
        """
        Update display order of a test case within a test plan.
        Used by the TestPlan.update_case_order RPC endpoint.
        """
        # OLD storage
        TestCasePlan.objects.filter(  # pylint:disable=objects-update-used
            case=case_id, plan=plan_id
        ).update(sortkey=sortkey)

        # NEW storage
        if plan_id in self._plan_cases and case_id in self._plan_cases[plan_id]:
            self._plan_cases[plan_id][case_id] = sortkey

        print(f"[TestPlanDAO] update_case_order: plan={plan_id}, case={case_id}, sortkey={sortkey}")

    def tree(self, plan):
        """
        Return the DFS-ordered ancestry tree for the given test plan.
        Used by the TestPlan.tree RPC endpoint.
        """
        # OLD storage (tree structure is derived from DB; no separate new storage)
        result = []
        for record in plan.tree_as_list():
            result.append(
                {
                    "id": record.pk,
                    "name": record.name,
                    "parent_id": record.parent_id,
                    "tree_depth": record.tree_depth,
                    "url": record.get_full_url(),
                }
            )

        print(f"[TestPlanDAO] tree: plan id={plan.pk}, {len(result)} node(s)")
        return result


test_plan_dao = TestPlanDAO()
