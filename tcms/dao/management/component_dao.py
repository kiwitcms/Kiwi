from tcms.management.models import Component

_COMPONENT_FIELDS = (
    "id",
    "name",
    "product",
    "initial_owner",
    "initial_qa_contact",
    "description",
)


class ComponentDAO:
    def __init__(self):
        # new storage: maps component_id (int) -> component dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, component):
        """Convert a Component object to a plain dict with public fields."""
        result = {field: getattr(component, field) for field in _COMPONENT_FIELDS}
        # store PKs, not related objects
        result["product"] = component.product_id
        result["initial_owner"] = component.initial_owner_id
        result["initial_qa_contact"] = component.initial_qa_contact_id
        # related field annotations matching filter()
        # "cases" is M2M — store None at save time (cases are linked separately)
        result["cases"] = None
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[ComponentDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[ComponentDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of component dicts matching query.
        Used by the Component.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            Component.objects.filter(**query)
            .values(*_COMPONENT_FIELDS, "cases")
            .order_by("id")
            .distinct()
        )

        # NEW storage - only components previously written through DAO
        new_result = [self._store[c["id"]] for c in old_result if c["id"] in self._store]

        if new_result:
            old_subset = [c for c in old_result if c["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[ComponentDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def filter_objects(self, **kwargs):
        """
        Return a Component queryset for use in views and templates.
        """
        return Component.objects.filter(**kwargs)

    def get_by_id(self, component_id):
        """
        Return a single Component object by primary key.
        """
        # OLD storage
        old_result = Component.objects.get(pk=component_id)

        # NEW storage
        new_result = self._store.get(component_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(f"[ComponentDAO] get_by_id: component id={component_id} not in new storage yet - skipping comparison")

        return old_result

    def get_by_name_and_product(self, name, product):
        """
        Return a single Component object by name and product.
        Used by TestCase.add_component RPC endpoint.
        """
        # OLD storage
        old_result = Component.objects.get(name=name, product=product)

        # NEW storage
        new_result = self._store.get(old_result.pk)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_name_and_product")
        else:
            print(f"[ComponentDAO] get_by_name_and_product: component not in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, component, update_fields=None):
        """
        Persist a Component object.
        Used by Component.create and Component.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            component.save(update_fields=update_fields)
        else:
            component.save()

        # NEW storage - store the current state of the component
        self._store[component.pk] = self._to_dict(component)

        print(f"[ComponentDAO] save: synced component id={component.pk} to new storage")
        return component


component_dao = ComponentDAO()
