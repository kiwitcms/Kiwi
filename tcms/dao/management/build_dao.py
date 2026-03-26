from tcms.management.models import Build

_BUILD_FIELDS = (
    "id",
    "name",
    "version",
    "is_active",
)


class BuildDAO:
    def __init__(self):
        # new storage: maps build_id (int) -> build dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, build):
        """Convert a Build object to a plain dict with public fields."""
        result = {field: getattr(build, field) for field in _BUILD_FIELDS}
        result["version"] = build.version_id  # store the PK int, not the related object
        # Fetch related names via DB query to match filter() output exactly (bypasses translation)
        extra = Build.objects.filter(pk=build.pk).values("version__value").first() or {}
        result.update(extra)
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[BuildDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[BuildDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of build dicts matching query.
        Used by the Build.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            Build.objects.filter(**query)
            .values(*_BUILD_FIELDS, "version__value")
            .order_by("version", "id")
            .distinct()
        )

        # NEW storage - only builds previously written through DAO
        new_result = [self._store[b["id"]] for b in old_result if b["id"] in self._store]

        if new_result:
            old_subset = [b for b in old_result if b["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[BuildDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def get_by_id(self, build_id):
        """
        Return a single Build object by primary key.
        """
        # OLD storage
        old_result = Build.objects.get(pk=build_id)

        # NEW storage
        new_result = self._store.get(build_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(f"[BuildDAO] get_by_id: build id={build_id} not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, build, update_fields=None):
        """
        Persist a Build object.
        Used by Build.create and Build.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            build.save(update_fields=update_fields)
        else:
            build.save()

        # NEW storage - store the current state of the build
        self._store[build.pk] = self._to_dict(build)

        print(f"[BuildDAO] save: synced build id={build.pk} to new storage")
        return build


build_dao = BuildDAO()
