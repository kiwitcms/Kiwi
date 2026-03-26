from tcms.bugs.models import Bug

_BUG_FIELDS = (
    "id",
    "summary",
    "created_at",
    "status",
    "reporter_id",
    "assignee_id",
    "product_id",
    "version_id",
    "build_id",
    "severity_id",
)


class BugDAO:
    def __init__(self):
        # new storage: maps bug_id (int) -> bug dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, bug):
        """Convert a Bug object to a plain dict with public fields."""
        return {field: getattr(bug, field) for field in _BUG_FIELDS}

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[BugDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[BugDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of bug dicts matching query.
        Used internally and by Bug.filter_canonical RPC endpoint.
        """
        # OLD storage
        old_result = list(
            Bug.objects.filter(**query)
            .values(*_BUG_FIELDS)
            .order_by("id")
            .distinct()
        )

        # NEW storage - only bugs previously written through DAO
        new_result = [self._store[b["id"]] for b in old_result if b["id"] in self._store]

        if new_result:
            old_subset = [b for b in old_result if b["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[BugDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def filter_with_names(self, query):
        """
        Return a list of bug dicts with related field names.
        Used by the Bug.filter RPC endpoint.
        """
        _NAME_FIELDS = (
            "pk",
            "summary",
            "created_at",
            "product__name",
            "version__value",
            "build__name",
            "reporter__username",
            "assignee__username",
            "severity__name",
            "severity__color",
            "severity__icon",
        )
        # OLD storage
        old_result = list(
            Bug.objects.filter(**query)
            .values(*_NAME_FIELDS)
            .distinct()
        )

        # NEW storage - compare IDs with what is tracked in _store
        new_ids = {b["pk"] for b in old_result if b["pk"] in self._store}
        if new_ids:
            print(f"[BugDAO] filter_with_names: {len(new_ids)} bug(s) also in new storage")
        else:
            print("[BugDAO] filter_with_names: no data in new storage yet - skipping comparison")

        return old_result

    def filter_canonical(self, query):
        """
        Return a list of bug dicts with FK IDs.
        Used by the Bug.filter_canonical RPC endpoint.
        """
        _CANONICAL_FIELDS = (
            "id",
            "summary",
            "created_at",
            "status",
            "reporter",
            "assignee",
            "product",
            "version",
            "build",
            "severity",
        )
        # OLD storage
        old_result = list(
            Bug.objects.filter(**query)
            .values(*_CANONICAL_FIELDS)
            .distinct()
        )

        # NEW storage - compare with _store
        new_result = [self._store[b["id"]] for b in old_result if b["id"] in self._store]

        if new_result:
            old_subset = [b for b in old_result if b["id"] in self._store]
            self._compare(old_subset, new_result, "filter_canonical")
        else:
            print("[BugDAO] filter_canonical: no data in new storage yet - skipping comparison")

        return old_result

    def get_by_id(self, bug_id):
        """
        Return a single Bug object by primary key.
        """
        # OLD storage
        old_result = Bug.objects.get(pk=bug_id)

        # NEW storage
        new_result = self._store.get(bug_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(f"[BugDAO] get_by_id: bug id={bug_id} not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, bug, update_fields=None):
        """
        Persist a Bug object.
        Used by Bug.create and Bug.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            bug.save(update_fields=update_fields)
        else:
            bug.save()

        # NEW storage - store the current state of the bug
        self._store[bug.pk] = self._to_dict(bug)

        print(f"[BugDAO] save: synced bug id={bug.pk} to new storage")
        return bug

    def remove(self, query):
        """
        Delete Bug objects matching query.
        Used by Bug.remove RPC endpoint.
        """
        # OLD storage
        deleted = Bug.objects.filter(**query).delete()
        print(f"[BugDAO] remove: deleted {deleted[0]} bug(s)")
        return deleted


bug_dao = BugDAO()
