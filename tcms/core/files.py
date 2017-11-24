# -*- coding: utf-8 -*-

import os

from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils.encoding import smart_str
from django.http import JsonResponse

from tcms.core.views import Prompt
from tcms.management.models import TestAttachment
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCaseAttachment
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TestPlanAttachment


@permission_required('management.add_testattachment')
def upload_file(request):
    if request.FILES.get('upload_file'):
        upload_file = request.FILES['upload_file']

        try:
            upload_file.name.encode('utf8')
        except UnicodeEncodeError:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Alert,
                info='Upload File name is not legal.',
                next='javascript:window.history.go(-1);',
            ))

        now = datetime.now()

        stored_name = '%s-%s-%s' % (request.user.username, now, upload_file.name)

        stored_file_name = os.path.join(
            settings.FILE_UPLOAD_DIR, stored_name).replace('\\', '/')
        stored_file_name = smart_str(stored_file_name)

        if upload_file._size > settings.MAX_UPLOAD_SIZE:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Alert,
                info='You upload entity is too large. \
                    Please ensure the file is less than %s bytes. \
                    ' % settings.MAX_UPLOAD_SIZE,
                next='javascript:window.history.go(-1);',
            ))

        # Create the upload directory when it's not exist
        try:
            os.listdir(settings.FILE_UPLOAD_DIR)
        except OSError:
            os.mkdir(settings.FILE_UPLOAD_DIR)

        # Write to a temporary file
        try:
            open(stored_file_name, 'ro')
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Alert,
                info='File named \'%s\' already exist in upload folder, \
                    please rename to another name for solve conflict.\
                    ' % upload_file.name,
                next='javascript:window.history.go(-1);',
            ))
        except IOError:
            pass

        dest = open(stored_file_name, 'wb+')
        for chunk in upload_file.chunks():
            dest.write(chunk)
        dest.close()

        # Write the file to database
        # store_file = open(upload_file_name, 'ro')
        ta = TestAttachment.objects.create(
            submitter_id=request.user.id,
            description=request.POST.get('description', None),
            file_name=upload_file.name,
            stored_name=stored_name,
            create_date=now,
            mime_type=upload_file.content_type
        )

        if request.POST.get('to_plan_id'):
            TestPlanAttachment.objects.create(
                plan_id=int(request.POST['to_plan_id']),
                attachment_id=ta.attachment_id,
            )

            return HttpResponseRedirect(
                reverse('plan-attachment', args=[request.POST['to_plan_id']])
            )
        elif request.POST.get('to_case_id'):
            TestCaseAttachment.objects.create(
                attachment_id=ta.attachment_id,
                case_id=int(request.POST['to_case_id'])
            )

            return HttpResponseRedirect(
                reverse('case-attachment', args=[request.POST['to_case_id']])
            )
    else:
        try:
            return HttpResponseRedirect(
                reverse('plan-attachment',
                        args=[request.POST['to_plan_id']])
            )
        except KeyError:
            return HttpResponseRedirect(
                reverse('case-attachment', args=[request.POST['to_case_id']])
            )


def check_file(request, file_id):
    import os
    from urllib import unquote
    from django.conf import settings
    from tcms.management.models import TestAttachment, TestAttachmentData

    try:
        attachment = TestAttachment.objects.get(attachment_id=file_id)
    except TestAttachment.DoesNotExist:
        raise Http404

    try:
        attachment = TestAttachment.objects.get(attachment_id=file_id)
        attachment_data = TestAttachmentData.objects.get(
            attachment__attachment_id=file_id
        )
        contents = attachment_data.contents
    except TestAttachmentData.DoesNotExist:
        if attachment.stored_name:
            stored_file_name = os.path.join(
                settings.FILE_UPLOAD_DIR, unquote(attachment.stored_name)
            ).replace('\\', '/')
            stored_file_name = stored_file_name.encode('utf-8')
            try:
                f = open(stored_file_name, 'ro')
                contents = f.read()
            except IOError as error:
                raise Http404(error)
        else:
            stored_file_name = os.path.join(
                settings.FILE_UPLOAD_DIR, unquote(attachment.file_name)
            ).replace('\\', '/')
            stored_file_name = stored_file_name.encode('utf-8')
            try:
                f = open(stored_file_name, 'ro')
                contents = f.read()
            except IOError as error:
                raise Http404(error)

    response = HttpResponse(contents, mimetype=str(attachment.mime_type))
    file_name = smart_str(attachment.file_name)
    response['Content-Disposition'] = \
        'attachment; filename="%s"' % file_name
    return response


def able_to_delete_attachment(request, file_id):
    """
    These are allowed to delete attachment -
        1. super user
        2. attachments's submitter
        3. testplan's author or owner
        4. testcase's owner
    """

    user = request.user
    if user.is_superuser:
        return True

    attach = TestAttachment.objects.get(attachment_id=file_id)
    if user.pk == attach.submitter_id:
        return True

    if 'from_plan' in request.GET:
        plan_id = int(request.GET['from_plan'])
        plan = TestPlan.objects.get(plan_id=plan_id)
        return user.pk == plan.owner_id or user.pk == plan.author_id

    if 'from_case' in request.GET:
        case_id = int(request.GET['from_case'])
        case = TestCase.objects.get(case_id=case_id)
        return user.pk == case.author_id

    return False


# Delete Attachment
def delete_file(request, file_id):
    ajax_response = {'rc': 0, 'response': 'ok'}
    DELEFAILURE = 1
    AUTHUNSUCCESS = 2

    state = able_to_delete_attachment(request, file_id)
    if not state:
        ajax_response['rc'] = AUTHUNSUCCESS
        ajax_response['response'] = 'auth_failure'
        return JsonResponse(ajax_response)

    # Delete plan's attachment
    if 'from_plan' in request.GET:
        try:
            plan_id = int(request.GET['from_plan'])
            attachment = TestPlanAttachment.objects.filter(attachment=file_id,
                                                           plan_id=plan_id)
            attachment.delete()
        except TestPlanAttachment.DoesNotExist:
            ajax_response['rc'] = DELEFAILURE
            ajax_response['response'] = 'failure'
        return JsonResponse(ajax_response)

    # Delete cases' attachment
    elif 'from_case' in request.GET:
        try:
            case_id = int(request.GET['from_case'])
            attachment = TestCaseAttachment.objects.filter(attachment=file_id,
                                                           case_id=case_id)
            attachment.delete()
        except TestCaseAttachment.DoesNotExist:
            ajax_response['rc'] = DELEFAILURE
            ajax_response['response'] = 'failure'

        return JsonResponse(ajax_response)
