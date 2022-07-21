#!/usr/bin/env python

import redminelib

# REST API is enabled by default in our container, otherwise go to
# Administration -> Settings -> API to enable it by hand
rpc = redminelib.Redmine(
    "http://bugtracker.kiwitcms.org:3000",
    username="admin",
    password="admin",
)


atodorov = rpc.user.create(
    login="atodorov",
    password="very-big-secret",
    firstname="Alex",
    lastname="Todorov",
    mail="atodorov@example.org",
)

# tracker & issue statuses must be configured before hand b/c
# Redmine API doesn't support creating them!
tracker = rpc.tracker.all()[0]

status = rpc.issue_status.all()[0]

# priority must also be configure before hand b/c Redmine doesn't
# expose creation via its API
priority = rpc.enumeration.filter(resource="issue_priorities")[0]

project = rpc.project.create(
    name="Integration with Kiwi TCMS",
    identifier="kiwitcms",
    tracker_ids=[tracker.id],
)

# b/c rpc.role doesn't have a .filter() method
for tester_role in rpc.role.all():
    if tester_role.name == "Tester":
        break

# make atodorov a member of the project so that we can assign issues to him
membership = rpc.project_membership.create(
    project_id=project.id,
    user_id=atodorov.id,
    role_ids=[tester_role.id],
)

# http://bugtracker.kiwitcms.org:3000/issues/1
issue = rpc.issue.create(
    subject="Hello Redmine",
    description="Created via API",
    project_id=project.id,
    tracker_id=tracker.id,
    status_id=status.id,
    priority_id=priority.id,
)
