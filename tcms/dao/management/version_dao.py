from tcms.management.models import Version

_VERSION_FIELDS = (
    "id",
    "value",
    "product",
)


class VersionDAO:
    def __init__(self):
        # new storage: maps version_id (int) -> version dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, version):
        """Convert a Version object to a plain dict with public fields."""
        result = {field: getattr(version, field) for field in _VERSION_FIELDS}
        result["product"] = version.product_id  # store PK, not related object
        # Fetch related names via DB query to match filter() output exactly (bypasses translation)
        extra = Version.objects.filter(pk=version.pk).values("product__name").first() or {}
        result.update(extra)
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[VersionDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[VersionDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of version dicts matching query.
        Used by the Version.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            Version.objects.filter(**query)
            .values(*_VERSION_FIELDS, "product__name")
            .order_by("product", "id")
            .distinct()
        )

        # NEW storage - only versions previously written through DAO
        new_result = [self._store[v["id"]] for v in old_result if v["id"] in self._store]

        if new_result:
            old_subset = [v for v in old_result if v["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[VersionDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, version, update_fields=None):
        """
        Persist a Version object.
        Used by Version.create and Version.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            version.save(update_fields=update_fields)
        else:
            version.save()

        # NEW storage - store the current state of the version
        self._store[version.pk] = self._to_dict(version)

        print(f"[VersionDAO] save: synced version id={version.pk} to new storage")
        return version


version_dao = VersionDAO()
