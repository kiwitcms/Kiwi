from django.forms.models import model_to_dict

from tcms.core.contrib.linkreference.models import LinkReference


class LinkReferenceDAO:
    def __init__(self):
        # new storage: maps execution_id (int) -> list of link dicts
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[LinkReferenceDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[LinkReferenceDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def get_links(self, query):
        """
        Return serialized LinkReference records matching query.
        Used by TestExecution.get_links RPC endpoint.
        """
        # OLD storage
        old_result = list(
            LinkReference.objects.filter(**query).values(
                "id",
                "name",
                "url",
                "execution",
                "created_on",
                "is_defect",
            )
        )

        # NEW storage — only links previously written through DAO
        execution_ids_in_result = {r["execution"] for r in old_result}
        new_result = []
        for eid in execution_ids_in_result:
            if eid in self._store:
                new_result.extend(self._store[eid])

        if new_result:
            self._compare(old_result, new_result, "get_links")
        else:
            print("[LinkReferenceDAO] get_links: no data in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, link):
        """
        Persist a LinkReference object and sync to new storage.
        Used by TestExecution.add_link RPC endpoint.
        """
        # OLD storage — object is already saved by the form; we just sync
        execution_id = link.execution_id
        if execution_id not in self._store:
            self._store[execution_id] = []
        self._store[execution_id].append(
            {
                "id": link.pk,
                "name": link.name,
                "url": link.url,
                "execution": execution_id,
                "created_on": link.created_on,
                "is_defect": link.is_defect,
            }
        )

        print(f"[LinkReferenceDAO] save: synced link id={link.pk} to new storage")
        return model_to_dict(link)

    def remove(self, query):
        """
        Delete LinkReference records matching query.
        Used by TestExecution.remove_link RPC endpoint.
        """
        # OLD storage
        LinkReference.objects.filter(**query).delete()

        # NEW storage — if query targets a specific execution, clear its store
        if "execution" in query:
            execution_id = query["execution"]
            self._store.pop(execution_id, None)
            print(f"[LinkReferenceDAO] remove: cleared new storage for execution id={execution_id}")
        else:
            print("[LinkReferenceDAO] remove: complex query - new storage not updated")


link_reference_dao = LinkReferenceDAO()
