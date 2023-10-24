# pylint: disable=unused-argument, objects-update-used


def change_assignee(rpc, new_issue, execution, user):
    """
    Note: user is the Kiwi TCMS user currently logged in,
          who is reporting the issue.
          Redmine integration is done via the "admin" account.

    We'll reasign to "atodorov" account in Redmine. In practice you will
    probably want to match user.username with your Redmine DB.

    :raises RuntimeError: when user not found in Redmine.
    """
    try:
        atodorov = rpc.user.filter(name="atodorov")[0]
    except Exception as err:
        raise RuntimeError("User 'atodorov' not found in Redmine") from err

    # Note: assignee needs to be a member of the project where issues are created
    # and needs to have a role with the `assignable` flag set to 1.
    rpc.issue.update(new_issue.id, assigned_to_id=atodorov.id)


def rpc_creds(issue_tracker):
    return ("tester", "test-me")


def rpc_no_creds(issue_tracker):
    return None
