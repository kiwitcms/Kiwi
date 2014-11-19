# -*- coding: utf-8 -*-
import datetime

from tcms.management.models import TestAttachment


def handle_uploaded_file(f, submitter_id, ):
    # Write to a temporary file
    dest = open('/tmp/' + f.name, 'wb+')
    for chunk in f.chunks():
        dest.write(chunk)
    dest.close()

    # Write the file to database
    TestAttachment.objects.create(
        submitter_id=submitter_id,
        description=None,
        filename=f.name,
        creation_ts=datetime.datetime.now()
    )
    return dest.name
