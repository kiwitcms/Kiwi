# -*- coding: utf-8 -*-

import io
import time

from attachments import views as attachment_views
from attachments.models import Attachment
from django.http import HttpRequest
from django.middleware.csrf import get_token
from mock import MagicMock

from tcms.core.utils import request_host_link


def get_attachments_for(request, obj):
    host_link = request_host_link(request)
    result = []
    for attachment in Attachment.objects.attachments_for_object(obj):
        result.append(
            {
                "pk": attachment.pk,
                "url": host_link + attachment.attachment_file.url,
                "owner_pk": attachment.creator.pk,
                "owner_username": attachment.creator.username,
                "date": attachment.created.isoformat(),
            }
        )
    return result


def encode_multipart(csrf_token, filename, b64content):
    """
    Build a multipart/form-data body with generated random boundary
    suitable for parsing by django.http.request.HttpRequest and
    the parser classes related to it!

    .. note::

        ``\\r\\n`` are expected! Do not change!
    """
    boundary = "----------%s" % int(time.time() * 1000)
    data = ["--%s" % boundary]

    data.append('Content-Disposition: form-data; name="csrfmiddlewaretoken"\r\n')
    data.append(csrf_token)
    data.append("--%s" % boundary)

    data.append(
        'Content-Disposition: form-data; name="attachment_file"; filename="%s"'
        % filename
    )
    data.append("Content-Type: application/octet-stream")
    data.append("Content-Transfer-Encoding: base64")
    data.append("Content-Length: %d\r\n" % len(b64content))
    data.append(b64content)

    data.append("--%s--\r\n" % boundary)
    return "\r\n".join(data), boundary


def request_for_upload(user, filename, b64content):
    """
    Return a request object containing all fields necessary for file
    upload as if it was sent by the browser.
    """
    request = HttpRequest()
    request.user = user
    request.method = "POST"
    request.content_type = "multipart/form-data"
    # because attachment.views.add_attachment() calls messages.success()
    request._messages = MagicMock()  # pylint: disable=protected-access

    data, boundary = encode_multipart(get_token(request), filename, b64content)

    request.META["CONTENT_TYPE"] = "multipart/form-data; boundary=%s" % boundary
    request.META["CONTENT_LENGTH"] = len(data)
    request._stream = io.BytesIO(data.encode())  # pylint: disable=protected-access

    # manually parse the input data and populate data attributes
    request._read_started = False  # pylint: disable=protected-access
    request._load_post_and_files()  # pylint: disable=protected-access
    request.POST = request._post  # pylint: disable=protected-access
    request.FILES = request._files  # pylint: disable=protected-access

    return request


def add_attachment(obj_id, app_model, user, filename, b64content):
    """
    High-level function which performs the attachment process
    by constructing an HttpRequest object and passing it to
    attachments.views.add_attachment() as if it came from the browser.
    """
    request = request_for_upload(user, filename, b64content)
    app, model = app_model.split(".")
    response = attachment_views.add_attachment(request, app, model, obj_id)
    if response.status_code == 404:
        raise Exception("Adding attachment to %s(%d) failed" % (app_model, obj_id))
