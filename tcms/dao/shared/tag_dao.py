from tcms.management.models import Tag


class TagDAO:
    def __init__(self):
        # new storage: maps (model_name, obj_id) -> set of tag names
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _key(self, model_obj):
        return (model_obj.__class__.__name__.lower(), model_obj.pk)

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[TagDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[TagDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def add_tag(self, model_obj, tag):
        """
        Add tag to a model object (TestCase, TestPlan, or TestRun).
        Calls the Django ORM add_tag method on the object.
        """
        # OLD storage
        model_obj.add_tag(tag)

        # NEW storage
        key = self._key(model_obj)
        if key not in self._store:
            self._store[key] = set()
        self._store[key].add(tag.name)

        print(f"[TagDAO] add_tag: added tag '{tag.name}' to {key}")

    def remove_tag(self, model_obj, tag):
        """
        Remove tag from a model object (TestCase, TestPlan, or TestRun).
        Calls the Django ORM remove_tag method on the object.
        """
        # OLD storage
        model_obj.remove_tag(tag)

        # NEW storage
        key = self._key(model_obj)
        if key in self._store:
            self._store[key].discard(tag.name)

        print(f"[TagDAO] remove_tag: removed tag '{tag.name}' from {key}")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def get_tags(self, model_obj):
        """
        Get all tags for a model object, comparing old and new storage.
        Returns list of {"id": ..., "name": ...} dicts.
        """
        # OLD storage
        old_result = list(model_obj.tag.values("id", "name"))
        old_names = {t["name"] for t in old_result}

        # NEW storage
        key = self._key(model_obj)
        new_result = self._store.get(key)

        if new_result is not None:
            self._compare(old_names, new_result, f"get_tags for {key}")
        else:
            print(f"[TagDAO] get_tags: {key} not in new storage yet - skipping comparison")

        return old_result

    @staticmethod
    def get_or_create(user, tag_name):
        """Wrapper around Tag.get_or_create for consistent access."""
        return Tag.get_or_create(user, tag_name)

    @staticmethod
    def get_by_name(tag_name):
        """Fetch a Tag by name from ORM."""
        return Tag.objects.get(name=tag_name)


tag_dao = TagDAO()
