from tcms.core.helpers import comments


class CommentDAO:
    def __init__(self):
        # new storage: maps (model_name, obj_id) -> list of comment dicts
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _key(self, model_obj):
        return (model_obj.__class__.__name__.lower(), model_obj.pk)

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[CommentDAO] MISMATCH in '{operation}':")
            print(f"  OLD count: {len(old)}")
            print(f"  NEW count: {len(new)}")
        else:
            print(f"[CommentDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def get_comments(self, model_obj):
        """
        Get all comments for the given model object.
        Returns a list of comment value dicts.
        """
        # OLD storage
        old_result = list(comments.get_comments(model_obj).values())

        # NEW storage
        key = self._key(model_obj)
        new_result = self._store.get(key)

        if new_result is not None:
            self._compare(old_result, new_result, f"get_comments for {key}")
        else:
            print(f"[CommentDAO] get_comments: {key} not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def add_comment(self, model_obj, comment_text, author, submit_date=None):
        """
        Add a comment to the given model object.
        Returns the serialized comment dict (model_to_dict).
        """
        from django.forms.models import model_to_dict

        # OLD storage
        created = comments.add_comment([model_obj], comment_text, author, submit_date)
        # always creates exactly one comment
        comment_obj = created[0]

        # NEW storage
        key = self._key(model_obj)
        if key not in self._store:
            self._store[key] = []
        self._store[key].append({"id": comment_obj.pk, "comment": comment_text})

        print(f"[CommentDAO] add_comment: added comment id={comment_obj.pk} to {key}")
        return model_to_dict(comment_obj)

    def remove_comment(self, model_obj, comment_id=None):
        """
        Remove all or specified comment(s) from the given model object.
        """
        # OLD storage
        to_be_deleted = comments.get_comments(model_obj)
        if comment_id:
            to_be_deleted = to_be_deleted.filter(pk=comment_id)
        to_be_deleted.delete()

        # NEW storage
        key = self._key(model_obj)
        if key in self._store:
            if comment_id:
                self._store[key] = [c for c in self._store[key] if c.get("id") != comment_id]
            else:
                self._store[key] = []

        print(f"[CommentDAO] remove_comment: removed comment(s) from {key}")


comment_dao = CommentDAO()
