# -*- coding: utf-8 -*-
"""
Shared functions for plan/case/run.

Most of these functions are use for Ajax.
"""
import datetime
import sys
import json
from distutils.util import strtobool

from django import http
from django.db.models import Q
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.forms import ValidationError
from django.dispatch import Signal
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from tcms.management.models import Component, Build, Version
from tcms.management.models import Priority
from tcms.management.models import TestTag
from tcms.testcases.models import TestCase, TestCaseBug
from tcms.testcases.models import Category
from tcms.testcases.models import TestCaseStatus
from tcms.testcases.views import get_selected_testcases
from tcms.testcases.views import plan_from_request_or_none
from tcms.testplans.models import TestPlan, TestCasePlan
from tcms.testruns import signals as run_watchers
from tcms.testruns.models import TestRun, TestCaseRun, TestCaseRunStatus
from tcms.core.helpers.comments import add_comment
from tcms.core.utils import string_to_list
from tcms.core.utils.validations import validate_bug_id

post_update = Signal(providing_args=["instances", "kwargs"])
post_update.connect(run_watchers.post_update_handler)


def check_permission(request, ctype):
    perm = '%s.change_%s' % tuple(ctype.split('.'))
    if request.user.has_perm(perm):
        return True
    return False


def strip_parameters(request_dict, skip_parameters):
    parameters = {}
    for k, v in request_dict.items():
        if k not in skip_parameters and v:
            parameters[str(k)] = v

    return parameters


@require_GET
def info(request):
    """Ajax responsor for misc information"""

    class Objects(object):
        __all__ = [
            'builds', 'categories', 'components', 'env_groups',
            'env_properties', 'env_values', 'tags', 'users', 'versions'
        ]

        def __init__(self, request, product_id=None):
            self.request = request
            try:
                self.product_id = int(product_id)
            except (ValueError, TypeError):
                self.product_id = 0
            self.internal_parameters = ('info_type', 'field', 'format')

        def builds(self):
            from tcms.management.models import Build

            try:
                _is_active = bool(strtobool(self.request.GET.get('is_active', 'False')))
            except (ValueError, TypeError):
                _is_active = False

            query = {
                'product_id': self.product_id,
                'is_active': _is_active
            }
            return Build.list(query)

        def categories(self):
            from tcms.testcases.models import Category

            return Category.objects.filter(product__id=self.product_id)

        def components(self):
            from tcms.management.models import Component

            return Component.objects.filter(product__id=self.product_id)

        def env_groups(self):
            from tcms.management.models import EnvGroup

            return EnvGroup.objects.all()

        def env_properties(self):
            from tcms.management.models import EnvGroup, EnvProperty

            if self.request.GET.get('env_group_id'):
                env_group = EnvGroup.objects.get(
                    id=self.request.GET['env_group_id']
                )
                return env_group.property.all()
            else:
                return EnvProperty.objects.all()

        def env_values(self):
            from tcms.management.models import EnvValue

            return EnvValue.objects.filter(
                property__id=self.request.GET.get('env_property_id')
            )

        def users(self):
            from django.contrib.auth.models import User

            query = strip_parameters(self.request.GET, self.internal_parameters)
            return User.objects.filter(**query)

        def versions(self):
            from tcms.management.models import Version

            return Version.objects.filter(product__id=self.product_id)

    objects = Objects(request=request, product_id=request.GET.get('product_id'))
    obj = getattr(objects, request.GET.get('info_type'), None)

    if obj:
        if request.GET.get('format') == 'ulli':
            field = request.GET.get('field', 'name')
            response_str = '<ul>'
            for o in obj().values(field):
                response_str += '<li>' + o.get(field, None) + '</li>'
            response_str += '</ul>'
            return HttpResponse(response_str)

        return HttpResponse(serializers.serialize(
            request.GET.get('format', 'json'),
            obj(),
            fields=('name', 'value')
        ))

    return HttpResponse('Unrecognizable infotype')


@require_GET
def form(request):
    """Response get form ajax call, most using in dialog"""

    # The parameters in internal_parameters will delete from parameters
    internal_parameters = ['app_form', 'format']
    parameters = strip_parameters(request.GET, internal_parameters)
    q_app_form = request.GET.get('app_form')
    q_format = request.GET.get('format')
    if not q_format:
        q_format = 'p'

    if not q_app_form:
        return HttpResponse('Unrecognizable app_form')

    # Get the form
    q_app, q_form = q_app_form.split('.')[0], q_app_form.split('.')[1]
    exec('from tcms.%s.forms import %s as form' % (q_app, q_form))
    try:
        __import__('tcms.%s.forms' % q_app)
    except ImportError:
        raise
    q_app_module = sys.modules['tcms.%s.forms' % q_app]
    form_class = getattr(q_app_module, q_form)
    form = form_class(initial=parameters)

    # Generate the HTML and reponse
    html = getattr(form, 'as_' + q_format)
    return HttpResponse(html())


def tag(request, template_name="management/get_tag.html"):
    """Get tags for test plan or test case"""

    class Objects(object):
        __all__ = ['plan', 'case', 'run']

        def __init__(self, request, template_name):
            self.request = request
            self.template_name = template_name
            for o in self.__all__:
                if request.GET.get(o):
                    self.object = o
                    self.object_pks = request.GET.getlist(o)
                    break

        def get(self):
            func = getattr(self, self.object)
            return func()

        def plan(self):
            return self.template_name, TestPlan.objects.filter(
                pk__in=self.object_pks)

        def case(self):
            return self.template_name, get_selected_testcases(self.request)

        def run(self):
            self.template_name = 'run/get_tag.html'
            return self.template_name, TestRun.objects.filter(
                pk__in=self.object_pks)

    class TagActions(object):
        __all__ = ['add', 'remove']

        def __init__(self, obj, tag):
            self.obj = obj
            self.tag = string_to_list(tag)
            self.request = request

        def add(self):
            for tag_str in self.tag:
                try:
                    tag, c = TestTag.objects.get_or_create(name=tag_str)
                    for o in self.obj:
                        o.add_tag(tag)
                except IntegrityError:
                    return "Error when adding %s " \
                           "Tag with this key already exists in the database." % self.tag
                except Exception:
                    return "Error when adding %s" % self.tag

            return True, self.obj

        def remove(self):
            self.obj = self.obj.filter(tag__name__in=self.tag).distinct()

            if not self.obj:
                return "Tags does not exist in current selected plan."

            for tag_str in self.tag:
                try:
                    tag = TestTag.objects.filter(name=tag_str)[0]
                except IndexError:
                    return "Tag %s does not exist in current selected plan." % tag_str
                for object in self.obj:
                    try:
                        object.remove_tag(tag)
                    except Exception:
                        return "Remove tag %s error." % tag
            return True, self.obj

    objects = Objects(request, template_name)
    template_name, obj = objects.get()

    q_tag = request.GET.get('tags')
    q_action = request.GET.get('a')
    if q_action:
        tag_actions = TagActions(obj=obj, tag=q_tag)
        func = getattr(tag_actions, q_action)
        response = func()
        if not response[0]:
            return HttpResponse(json.dumps({'response': response, 'rc': 1}))

    del q_tag, q_action

    # Response to batch operations
    if request.GET.get('t') == 'json':
        if request.GET.get('f') == 'serialized':
            return HttpResponse(
                # FIXME: this line of code depends on the existence of `a`
                # argument in query string. So, if a does not appear in the
                # query string, error will happen here
                serializers.serialize(request.GET['t'], response[1])
            )

        return HttpResponse(json.dumps({'response': 'ok'}))

    # Response the single operation
    if len(obj) == 1:
        tags = obj[0].tag.all()
        tags = tags.extra(select={
            'num_plans':
                'SELECT COUNT(*) FROM test_plan_tags '
                'WHERE test_tags.tag_id = test_plan_tags.tag_id',
            'num_cases':
                'SELECT COUNT(*) FROM test_case_tags '
                'WHERE test_tags.tag_id = test_case_tags.tag_id',
            'num_runs':
                'SELECT COUNT(*) FROM test_run_tags '
                'WHERE test_tags.tag_id = test_run_tags.tag_id',
        })

        context_data = {
            'tags': tags,
            'object': obj[0],
        }
        return render(request, template_name, context_data)
    return HttpResponse('')


def get_value_by_type(val, v_type):
    '''
    Exampls:
    1. get_value_by_type('True', 'bool')
    (1, None)
    2. get_value_by_type('19860624 123059', 'datetime')
    (datetime.datetime(1986, 6, 24, 12, 30, 59), None)
    3. get_value_by_type('5', 'int')
    ('5', None)
    4. get_value_by_type('string', 'str')
    ('string', None)
    5. get_value_by_type('everything', 'None')
    (None, None)
    6. get_value_by_type('buggy', 'buggy')
    (None, 'Unsupported value type.')
    7. get_value_by_type('string', 'int')
    (None, "invalid literal for int() with base 10: 'string'")
    '''
    value = error = None

    def get_time(time):
        DT = datetime.datetime
        if time == 'NOW':
            return DT.now()
        return DT.strptime(time, '%Y%m%d %H%M%S')

    pipes = {
        # Temporary solution is convert all of data to str
        # 'bool': lambda x: x == 'True',
        'bool': lambda x: x == 'True' and 1 or 0,
        'datetime': get_time,
        'int': lambda x: str(int(x)),
        'str': lambda x: str(x),
        'None': lambda x: None,
    }
    pipe = pipes.get(v_type, None)
    if pipe is None:
        error = 'Unsupported value type.'
    else:
        try:
            value = pipe(val)
        except Exception as e:
            error = str(e)
    return value, error


def say_no(error_msg):
    ajax_response = {'rc': 1, 'response': error_msg}
    return HttpResponse(json.dumps(ajax_response))


def say_yes():
    return HttpResponse(json.dumps({'rc': 0, 'response': 'ok'}))


# Deprecated. Not flexible.
@require_POST
def update(request):
    '''
    Generic approach to update a model,\n
    based on contenttype.
    '''
    now = datetime.datetime.now()

    data = request.POST.copy()
    ctype = data.get("content_type")
    vtype = data.get('value_type', 'str')
    object_pk_str = data.get("object_pk")
    field = data.get('field')
    value = data.get('value')

    object_pk = [int(a) for a in object_pk_str.split(',')]

    if not field or not value or not object_pk or not ctype:
        return say_no(
            'Following fields are required - content_type, '
            'object_pk, field and value.')

    # Convert the value type
    # FIXME: Django bug here: update() keywords must be strings
    field = str(field)

    value, error = get_value_by_type(value, vtype)
    if error:
        return say_no(error)
    has_perms = check_permission(request, ctype)
    if not has_perms:
        return say_no('Permission Dinied.')

    model = apps.get_model(*ctype.split(".", 1))
    targets = model._default_manager.filter(pk__in=object_pk)

    if not targets:
        return say_no('No record found')
    if not hasattr(targets[0], field):
        return say_no('%s has no field %s' % (ctype, field))

    if hasattr(targets[0], 'log_action'):
        for t in targets:
            try:
                t.log_action(
                    who=request.user,
                    action='Field %s changed from %s to %s.' % (
                        field, getattr(t, field), value
                    )
                )
            except (AttributeError, User.DoesNotExist):
                pass
    objects_update(targets, **{field: value})

    if hasattr(model, 'mail_scene'):
        mail_context = model.mail_scene(
            objects=targets, field=field, value=value, ctype=ctype,
            object_pk=object_pk,
        )
        if mail_context:
            from tcms.core.utils.mailto import mailto

            mail_context['context']['user'] = request.user
            try:
                mailto(**mail_context)
            except Exception:
                pass

    # Special hacking for updating test case run status
    if ctype == 'testruns.testcaserun' and field == 'case_run_status':
        for t in targets:
            field = 'close_date'
            t.log_action(
                who=request.user,
                action='Field %s changed from %s to %s.' % (
                    field, getattr(t, field), now
                )
            )
            if t.tested_by != request.user:
                field = 'tested_by'
                t.log_action(
                    who=request.user,
                    action='Field %s changed from %s to %s.' % (
                        field, getattr(t, field), request.user
                    )
                )

            field = 'assignee'
            try:
                assignee = t.assginee
                if assignee != request.user:
                    t.log_action(
                        who=request.user,
                        action='Field %s changed from %s to %s.' % (
                            field, getattr(t, field), request.user
                        )
                    )
                    # t.assignee = request.user
                t.save()
            except (AttributeError, User.DoesNotExist):
                pass
        targets.update(close_date=now, tested_by=request.user)
    return say_yes()


@require_POST
def update_case_run_status(request):
    '''
    Update Case Run status.
    '''
    now = datetime.datetime.now()

    data = request.POST.copy()
    ctype = data.get("content_type")
    vtype = data.get('value_type', 'str')
    object_pk_str = data.get("object_pk")
    field = data.get('field')
    value = data.get('value')

    object_pk = [int(a) for a in object_pk_str.split(',')]

    if not field or not value or not object_pk or not ctype:
        return say_no(
            'Following fields are required - content_type, '
            'object_pk, field and value.')

    # Convert the value type
    # FIXME: Django bug here: update() keywords must be strings
    field = str(field)

    value, error = get_value_by_type(value, vtype)
    if error:
        return say_no(error)
    has_perms = check_permission(request, ctype)
    if not has_perms:
        return say_no('Permission Dinied.')

    model = apps.get_model(*ctype.split(".", 1))
    targets = model._default_manager.filter(pk__in=object_pk)

    if not targets:
        return say_no('No record found')
    if not hasattr(targets[0], field):
        return say_no('%s has no field %s' % (ctype, field))

    if hasattr(targets[0], 'log_action'):
        for t in targets:
            try:
                t.log_action(
                    who=request.user,
                    action='Field {} changed from {} to {}.'.format(
                        field,
                        getattr(t, field),
                        TestCaseRunStatus.id_to_string(value),
                    )
                )
            except (AttributeError, User.DoesNotExist):
                pass
    objects_update(targets, **{field: value})

    if hasattr(model, 'mail_scene'):
        from tcms.core.utils.mailto import mailto

        mail_context = model.mail_scene(
            objects=targets, field=field, value=value, ctype=ctype,
            object_pk=object_pk,
        )
        if mail_context:
            mail_context['context']['user'] = request.user
            try:
                mailto(**mail_context)
            except Exception:
                pass

    # Special hacking for updating test case run status
    if ctype == 'testruns.testcaserun' and field == 'case_run_status':
        for t in targets:
            field = 'close_date'
            t.log_action(
                who=request.user,
                action='Field %s changed from %s to %s.' % (
                    field, getattr(t, field), now
                )
            )
            if t.tested_by != request.user:
                field = 'tested_by'
                t.log_action(
                    who=request.user,
                    action='Field %s changed from %s to %s.' % (
                        field, getattr(t, field), request.user
                    )
                )

            field = 'assignee'
            try:
                assignee = t.assginee
                if assignee != request.user:
                    t.log_action(
                        who=request.user,
                        action='Field %s changed from %s to %s.' % (
                            field, getattr(t, field), request.user
                        )
                    )
                    # t.assignee = request.user
                t.save()
            except (AttributeError, User.DoesNotExist):
                pass
        targets.update(close_date=now, tested_by=request.user)

    return HttpResponse(json.dumps({'rc': 0, 'response': 'ok'}))


class ModelUpdateActions(object):
    """Abstract class defining interfaces to update a model properties"""


class TestCaseUpdateActions(ModelUpdateActions):
    '''Actions to update each possible proprety of TestCases

    Define your own method named _update_[property name] to hold specific
    update logic.
    '''

    ctype = 'testcases.testcase'

    def __init__(self, request):
        self.request = request
        self.target_field = request.POST.get('target_field')
        self.new_value = request.POST.get('new_value')

    def get_update_action(self):
        return getattr(self, '_update_%s' % self.target_field, None)

    def update(self):
        has_perms = check_permission(self.request, self.ctype)
        if not has_perms:
            return say_no("You don't have enough permission to update TestCases.")

        action = self.get_update_action()
        if action is not None:
            try:
                resp = action()
                self._sendmail()
            except ObjectDoesNotExist as err:
                return say_no(str(err))
            except Exception:
                # TODO: besides this message to users, what happening should be
                # recorded in the system log.
                return say_no('Update failed. Please try again or request '
                              'support from your organization.')
            else:
                if resp is None:
                    resp = say_yes()
                return resp
        return say_no('Not know what to update.')

    def get_update_targets(self):
        """Get selected cases to update their properties"""
        case_ids = map(int, self.request.POST.getlist('case'))
        self._update_objects = TestCase.objects.filter(pk__in=case_ids)
        return self._update_objects

    def get_plan(self, pk_enough=True):
        try:
            return plan_from_request_or_none(self.request, pk_enough)
        except Http404:
            return None

    def _sendmail(self):
        mail_context = TestCase.mail_scene(objects=self._update_objects,
                                           field=self.target_field,
                                           value=self.new_value)
        if mail_context:
            from tcms.core.utils.mailto import mailto

            mail_context['context']['user'] = self.request.user
            try:
                mailto(**mail_context)
            except Exception:
                pass

    def _update_priority(self):
        exists = Priority.objects.filter(pk=self.new_value).exists()
        if not exists:
            raise ObjectDoesNotExist('The priority you specified to change '
                                     'does not exist.')
        self.get_update_targets().update(**{str(self.target_field): self.new_value})

    def _update_default_tester(self):
        try:
            user = User.objects.get(Q(username=self.new_value) | Q(email=self.new_value))
        except User.DoesNotExist:
            raise ObjectDoesNotExist('Default tester not found!')
        self.get_update_targets().update(**{str(self.target_field): user.pk})

    def _update_case_status(self):
        try:
            new_status = TestCaseStatus.objects.get(pk=self.new_value)
        except TestCaseStatus.DoesNotExist:
            raise ObjectDoesNotExist('The status you choose does not exist.')

        update_object = self.get_update_targets()
        if not update_object:
            return say_no('No record(s) found')

        for testcase in update_object:
            if hasattr(testcase, 'log_action'):
                testcase.log_action(
                    who=self.request.user,
                    action='Field %s changed from %s to %s.' % (
                        self.target_field, testcase.case_status, new_status.name
                    )
                )
        update_object.update(**{str(self.target_field): self.new_value})

        # ###
        # Case is moved between Cases and Reviewing Cases tabs accoding to the
        # change of status. Meanwhile, the number of cases with each status
        # should be updated also.

        try:
            plan = plan_from_request_or_none(self.request)
        except Http404:
            return say_no("No plan record found.")
        else:
            if plan is None:
                return say_no('No plan record found.')

        confirm_status_name = 'CONFIRMED'
        plan.run_case = plan.case.filter(case_status__name=confirm_status_name)
        plan.review_case = plan.case.exclude(case_status__name=confirm_status_name)
        run_case_count = plan.run_case.count()
        case_count = plan.case.count()
        # FIXME: why not calculate review_case_count or run_case_count by using
        # substraction, which saves one SQL query.
        review_case_count = plan.review_case.count()

        return http.JsonResponse({
            'rc': 0, 'response': 'ok',
            'run_case_count': run_case_count,
            'case_count': case_count,
            'review_case_count': review_case_count,
        })

    def _update_sortkey(self):
        try:
            sortkey = int(self.new_value)
            if sortkey < 0 or sortkey > 32300:
                return say_no('New sortkey is out of range [0, 32300].')
        except ValueError:
            return say_no('New sortkey is not an integer.')
        plan = plan_from_request_or_none(self.request, pk_enough=True)
        if plan is None:
            return say_no('No plan record found.')
        update_targets = self.get_update_targets()

        # ##
        # MySQL does not allow to exeucte UPDATE statement that contains
        # subquery querying from same table. In this case, OperationError will
        # be raised.
        offset = 0
        step_length = 500
        queryset_filter = TestCasePlan.objects.filter
        data = {self.target_field: sortkey}
        while 1:
            sub_cases = update_targets[offset:offset + step_length]
            case_pks = [case.pk for case in sub_cases]
            if len(case_pks) == 0:
                break
            queryset_filter(plan=plan, case__in=case_pks).update(**data)
            # Move to next batch of cases to change.
            offset += step_length

    def _update_reviewer(self):
        reviewers = User.objects.filter(username=self.new_value).values_list('pk', flat=True)
        if not reviewers:
            err_msg = 'Reviewer %s is not found' % self.new_value
            raise ObjectDoesNotExist(err_msg)
        self.get_update_targets().update(**{str(self.target_field): reviewers[0]})


# NOTE: what permission is necessary
# FIXME: find a good chance to map all TestCase property change request to this
@require_POST
def update_cases_default_tester(request):
    '''Update default tester upon selected TestCases'''
    proxy = TestCaseUpdateActions(request)
    return proxy.update()


update_cases_priority = update_cases_default_tester
update_cases_case_status = update_cases_default_tester
update_cases_sortkey = update_cases_default_tester
update_cases_reviewer = update_cases_default_tester


@require_POST
def comment_case_runs(request):
    """
    Add comment to one or more caseruns at a time.
    """
    data = request.POST.copy()
    comment = data.get('comment', None)
    if not comment:
        return say_no('Comments needed')
    run_ids = [i for i in data.get('run', '').split(',') if i]
    if not run_ids:
        return say_no('No runs selected.')
    runs = TestCaseRun.objects.filter(pk__in=run_ids).only('pk')
    if not runs:
        return say_no('No caserun found.')
    add_comment(runs, comment, request.user)
    return say_yes()


def clean_bug_form(request):
    '''
    Verify the form data, return a tuple\n
    (None, ERROR_MSG) on failure\n
    or\n
    (data_dict, '') on success.\n
    '''
    data = {}
    try:
        data['bugs'] = request.GET.get('bug_id', '').split(',')
        data['runs'] = map(int, request.GET.get('case_runs', '').split(','))
    except (TypeError, ValueError) as e:
        return (None, 'Please specify only integers for bugs, '
                      'caseruns(using comma to seperate IDs), '
                      'and bug_system. (DEBUG INFO: %s)' % str(e))

    data['bug_system_id'] = int(request.GET.get('bug_system_id', 1))

    if request.GET.get('a') not in ('add', 'remove'):
        return (None, 'Actions only allow "add" and "remove".')
    else:
        data['action'] = request.GET.get('a')
    data['bz_external_track'] = True if request.GET.get('bz_external_track',
                                                        False) else False

    return (data, '')


def update_bugs_to_caseruns(request):
    '''
    Add one or more bugs to or remove that from\n
    one or more caserun at a time.
    '''
    data, error = clean_bug_form(request)
    if error:
        return say_no(error)
    runs = TestCaseRun.objects.filter(pk__in=data['runs'])
    bug_system_id = data['bug_system_id']
    bug_ids = data['bugs']

    try:
        validate_bug_id(bug_ids, bug_system_id)
    except ValidationError as e:
        return say_no(str(e))

    bz_external_track = data['bz_external_track']
    action = data['action']
    try:
        if action == "add":
            for run in runs:
                for bug_id in bug_ids:
                    run.add_bug(bug_id=bug_id,
                                bug_system_id=bug_system_id,
                                bz_external_track=bz_external_track)
        else:
            bugs = TestCaseBug.objects.filter(bug_id__in=bug_ids)
            for run in runs:
                for bug in bugs:
                    if bug.case_run_id == run.pk:
                        run.remove_bug(bug.bug_id, run.pk)
    except Exception as e:
        return say_no(str(e))
    return say_yes()


def get_prod_related_objs(p_pks, target):
    '''
    Get Component, Version, Category, and Build\n
    Return [(id, name), (id, name)]
    '''
    ctypes = {
        'component': (Component, 'name'),
        'version': (Version, 'value'),
        'build': (Build, 'name'),
        'category': (Category, 'name'),
    }
    results = ctypes[target][0]._default_manager.filter(product__in=p_pks)
    attr = ctypes[target][1]
    results = [(r.pk, getattr(r, attr)) for r in results]
    return results


def get_prod_related_obj_json(request):
    '''
    View for updating product drop-down\n
    in a Ajax way.
    '''
    data = request.GET.copy()
    target = data.get('target', None)
    p_pks = data.get('p_ids', None)
    sep = data.get('sep', None)
    # py2.6: all(*values) => boolean ANDs
    if target and p_pks and sep:
        p_pks = [k for k in p_pks.split(sep) if k]
        res = get_prod_related_objs(p_pks, target)
    else:
        res = []
    return HttpResponse(json.dumps(res))


def objects_update(objects, **kwargs):
    objects.update(**kwargs)
    kwargs['instances'] = objects
    if objects.model.__name__ == TestCaseRun.__name__ and kwargs.get(
            'case_run_status', None):
        post_update.send(sender=None, **kwargs)
