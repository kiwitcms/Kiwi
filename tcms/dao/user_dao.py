from django.contrib.auth import get_user_model

from tcms.utils import user as user_utils

User = get_user_model()  # pylint: disable=invalid-name

# Fields we expose publicly (no password, no sensitive internals)
_USER_FIELDS = (
    "email",
    "first_name",
    "id",
    "is_active",
    "is_staff",
    "is_superuser",
    "last_name",
    "username",
)


class UserDAO:
    def __init__(self):
        # new storage: maps user_id (int) -> user dict
        self._store = {}

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _to_dict(self, user):
        """Convert a User object to a plain dict with public fields."""
        return {field: getattr(user, field) for field in _USER_FIELDS}

    def _compare(self, old, new, operation):
        """Log whether old and new storage returned the same result."""
        if old != new:
            print(f"[UserDAO] MISMATCH in '{operation}':")
            print(f"  OLD: {old}")
            print(f"  NEW: {new}")
        else:
            print(f"[UserDAO] OK '{operation}': results match")

    # ------------------------------------------------------------------
    # READ operations
    # ------------------------------------------------------------------

    def filter(self, query):
        """
        Return a list of user dicts matching query.
        Used by the User.filter RPC endpoint.
        """
        # OLD storage
        old_result = list(
            User.objects.filter(**query)
            .values(*_USER_FIELDS)
            .order_by("id")
            .distinct()
        )

        # NEW storage - only users previously written through DAO
        new_result = [self._store[u["id"]] for u in old_result if u["id"] in self._store]

        if new_result:
            self._compare(old_result, new_result, "filter")
        else:
            print("[UserDAO] filter: no data in new storage yet - skipping comparison")

        return old_result

    def get_by_id(self, user_id):
        """
        Return a single User object by primary key.
        Used by User.update RPC endpoint.
        """
        # OLD storage
        old_result = User.objects.get(pk=user_id)

        # NEW storage
        new_result = self._store.get(user_id)

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_id")
        else:
            print(f"[UserDAO] get_by_id: user id={user_id} not in new storage yet - skipping comparison")

        return old_result

    def get_by_username(self, username):
        """
        Return a single User object by username.
        Used by User.join_group RPC endpoint.
        """
        # OLD storage
        old_result = User.objects.get(username=username)

        # NEW storage
        new_result = next(
            (u for u in self._store.values() if u.get("username") == username),
            None,
        )

        if new_result is not None:
            self._compare(self._to_dict(old_result), new_result, "get_by_username")
        else:
            print(f"[UserDAO] get_by_username: '{username}' not in new storage yet - skipping comparison")

        return old_result

    def filter_objects(self, query):
        """
        Return a list of User objects matching query.
        Used internally by deactivate (needs objects, not dicts).
        """
        # OLD storage
        return list(User.objects.filter(**query))

    # ------------------------------------------------------------------
    # WRITE operations
    # ------------------------------------------------------------------

    def save(self, user, update_fields=None):
        """
        Persist a User object.
        Used by User.update RPC endpoint.
        """
        # OLD storage
        if update_fields:
            user.save(update_fields=update_fields)
        else:
            user.save()

        # NEW storage - store the current state of the user
        self._store[user.pk] = self._to_dict(user)

        print(f"[UserDAO] save: synced user id={user.pk} to new storage")
        return user

    def deactivate(self, user):
        """
        Deactivate a user (sets is_active=False, clears permissions/groups).
        Used by User.deactivate RPC endpoint.
        """
        # OLD storage
        user_utils.deactivate(user)

        # NEW storage
        if user.pk in self._store:
            self._store[user.pk]["is_active"] = False
        else:
            self._store[user.pk] = self._to_dict(user)

        print(f"[UserDAO] deactivate: synced user id={user.pk} to new storage")

    def add_to_group(self, user, group):
        """
        Add a user to a group.
        Used by User.join_group RPC endpoint.
        """
        # OLD storage
        user.groups.add(group)

        # NEW storage - groups are not tracked in our simple dict yet
        print(
            f"[UserDAO] add_to_group: user id={user.pk} -> group '{group.name}' "
            f"(groups not tracked in new storage yet)"
        )


user_dao = UserDAO()
