"""
PropertyDAO wraps property CRUD for TestCase, TestRun, and TestExecution.

Each model has its own Property model:
  - tcms.testcases.models.Property  (FK: case)
  - tcms.testruns.models.Property   (FK: run)
  - tcms.testruns.models.TestExecutionProperty  (FK: execution)

The DAO is parameterized per model type via static factory methods.
"""
from django.forms.models import model_to_dict


class PropertyDAO:
    def __init__(self, model_class, fk_field, label):
        """
        :param model_class: The Django model class for properties (e.g. testcases.Property)
        :param fk_field: The FK field name on the property model (e.g. "case_id", "run_id")
        :param label: Human-readable label for logging (e.g. "TestCaseProperty")
        """
        self._model = model_class
        self._fk_field = fk_field
        self._label = label
        # new storage: maps obj_id -> list of {"name": ..., "value": ...}
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[{self._label}] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[{self._label}] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query, value_fields, order_by):
        """
        Return serialized property records matching query.
        value_fields: tuple of field names to include in .values()
        order_by: tuple of order-by fields
        """
        # OLD storage
        old_result = list(
            self._model.objects.filter(**query)
            .values(*value_fields)
            .order_by(*order_by)
            .distinct()
        )

        # NEW storage — only objects previously written through DAO
        # Extract all obj_ids from the result
        obj_id_field = self._fk_field.replace("_id", "")  # e.g. "case", "run", "execution"
        obj_ids_in_result = {r[obj_id_field] for r in old_result}
        new_result = []
        for oid in obj_ids_in_result:
            if oid in self._store:
                new_result.extend(self._store[oid])

        if new_result:
            self._compare(old_result, new_result, "filter")
        else:
            print(f"[{self._label}] filter: no data in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def get_or_create(self, obj_id, name, value):
        """
        Create a property if it doesn't exist (duplicates skipped).
        Returns serialized property dict.
        """
        # OLD storage
        kwargs = {self._fk_field: obj_id, "name": name, "value": value}
        prop, created = self._model.objects.get_or_create(**kwargs)

        # NEW storage
        if obj_id not in self._store:
            self._store[obj_id] = []
        entry = {"name": name, "value": value}
        if entry not in self._store[obj_id]:
            self._store[obj_id].append(entry)

        action = "created" if created else "already existed"
        print(f"[{self._label}] get_or_create: property ({name}={value}) for id={obj_id} {action}")
        return model_to_dict(prop)

    def remove(self, query):
        """
        Delete property records matching query.
        """
        # OLD storage
        self._model.objects.filter(**query).delete()

        # NEW storage — rebuild store entries from remaining DB state
        # (simple approach: clear any affected entries from the in-memory store)
        # We can't easily know which store entries were deleted without querying,
        # so we mark the affected objects as needing refresh by removing them.
        obj_id_field = self._fk_field  # e.g. "case_id"
        if obj_id_field in query:
            obj_id = query[obj_id_field]
            self._store.pop(obj_id, None)
            print(f"[{self._label}] remove: cleared new storage for id={obj_id}")
        else:
            print(f"[{self._label}] remove: complex query - new storage not updated")


# Per-model singleton instances
def _make_testcase_property_dao():
    from tcms.testcases.models import Property
    return PropertyDAO(Property, "case_id", "TestCasePropertyDAO")


def _make_testrun_property_dao():
    from tcms.testruns.models import Property
    return PropertyDAO(Property, "run_id", "TestRunPropertyDAO")


def _make_testexecution_property_dao():
    from tcms.testruns.models import TestExecutionProperty
    return PropertyDAO(TestExecutionProperty, "execution_id", "TestExecutionPropertyDAO")


testcase_property_dao = _make_testcase_property_dao()
testrun_property_dao = _make_testrun_property_dao()
testexecution_property_dao = _make_testexecution_property_dao()
