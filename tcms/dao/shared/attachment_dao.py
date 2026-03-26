from tcms.rpc import utils


class AttachmentDAO:
    def __init__(self):
        # new storage: maps (model_name, obj_id) -> list of attachment metadata dicts
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _key(self, model_obj):
        return (model_obj.__class__.__name__.lower(), model_obj.pk)

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        old_ids = {a.get("id") for a in old}
        new_ids = {a.get("id") for a in new}
        if old_ids != new_ids:
            print(f"[AttachmentDAO] MISMATCH in '{operation}':")
            print(f"  OLD ids: {old_ids}")
            print(f"  NEW ids: {new_ids}")
        else:
            print(f"[AttachmentDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def list_attachments(self, request, model_obj):
        """
        List attachments for the given model object.
        Returns a list of attachment info dicts with download URLs.
        """
        # OLD storage
        old_result = utils.get_attachments_for(request, model_obj)

        # NEW storage
        key = self._key(model_obj)
        new_result = self._store.get(key)

        if new_result is not None:
            self._compare(old_result, new_result, f"list_attachments for {key}")
        else:
            print(f"[AttachmentDAO] list_attachments: {key} not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def add_attachment(self, obj_id, model_label, user, filename, b64content):
        """
        Add attachment to a model object.
        model_label is e.g. "testcases.TestCase", "testplans.TestPlan", etc.
        """
        # OLD storage
        utils.add_attachment(obj_id, model_label, user, filename, b64content)

        # NEW storage - record the attachment metadata for future comparison
        # We cannot track a full URL here (it depends on the request), so we
        # record filename keyed by model and id
        key = (model_label.split(".")[-1].lower(), obj_id)
        if key not in self._store:
            self._store[key] = []
        self._store[key].append({"filename": filename})

        print(f"[AttachmentDAO] add_attachment: added '{filename}' to {key}")


attachment_dao = AttachmentDAO()
