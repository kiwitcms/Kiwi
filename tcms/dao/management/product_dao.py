from tcms.management.models import Product

_PRODUCT_FIELDS = (
    "id",
    "name",
    "description",
    "classification",
)


class ProductDAO:
    def __init__(self):
        # new storage: maps product_id (int) -> product dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, product):
        """Convert a Product object to a plain dict with public fields."""
        result = {field: getattr(product, field) for field in _PRODUCT_FIELDS}
        result["classification"] = product.classification_id  # store PK, not related object
        return result

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[ProductDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[ProductDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of product dicts matching query.
        Used by the Product.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            Product.objects.filter(**query)
            .values(*_PRODUCT_FIELDS)
            .order_by("id")
            .distinct()
        )

        # NEW storage - only products previously written through DAO
        new_result = [self._store[p["id"]] for p in old_result if p["id"] in self._store]

        if new_result:
            old_subset = [p for p in old_result if p["id"] in self._store]
            self._compare(old_subset, new_result, "filter")
        else:
            print("[ProductDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, product, update_fields=None):
        """
        Persist a Product object.
        Used by Product.create and Product.update RPC endpoints.
        """
        # OLD storage
        if update_fields:
            product.save(update_fields=update_fields)
        else:
            product.save()

        # NEW storage - store the current state of the product
        self._store[product.pk] = self._to_dict(product)

        print(f"[ProductDAO] save: synced product id={product.pk} to new storage")
        return product


product_dao = ProductDAO()
