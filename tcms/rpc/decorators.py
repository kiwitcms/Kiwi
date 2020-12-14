from modernrpc.auth import set_authentication_predicate


def permissions_required(perm):
    def check_perms(request, permissions):  # pylint: disable=nested-function-found
        if isinstance(permissions, str):
            permissions = (permissions,)

        # check if the user has the permission (even anon users)
        return request.user.has_perms(permissions)

    return set_authentication_predicate(check_perms, [perm])
