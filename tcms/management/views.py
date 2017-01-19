# -*- coding: utf-8 -*-

from itertools import groupby

try:
    from django.db import IntegrityError
except:
    pass

from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import json

from tcms.core.logs.models import TCMSLogModel
from tcms.core.utils import QuerySetIterationProxy
from tcms.management.models import TCMSEnvGroup
from tcms.management.models import TCMSEnvGroupPropertyMap
from tcms.management.models import TCMSEnvProperty
from tcms.management.models import TCMSEnvValue

MODULE_NAME = "management"


def environment_groups(request, template_name='environment/groups.html'):
    """
    Environements list
    """

    env_groups = TCMSEnvGroup.objects
    # Initial the response to browser
    ajax_response = {'rc': 0, 'response': 'ok'}

    has_perm = request.user.has_perm
    user_action = request.REQUEST.get('action')

    # Add action
    if user_action == 'add':
        if not has_perm('management.add_tcmsenvgroup'):
            ajax_response['response'] = 'Permission denied.'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        group_name = request.REQUEST.get('name')

        # Get the group name of envrionment from javascript
        if not group_name:
            ajax_response['response'] = 'Environment group name is required.'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        try:
            env = env_groups.create(name=group_name,
                                    manager_id=request.user.id,
                                    modified_by_id=None)
            env.log_action(who=request.user,
                           action='Initial env group %s' % env.name)
            ajax_response['id'] = env.id
            return HttpResponse(json.dumps(ajax_response))
        except IntegrityError, error:
            if error[1].startswith('Duplicate'):
                response_msg = 'Environment group named \'%s\' already ' \
                    'exists, please select another name.' % group_name
                ajax_response['response'] = response_msg
            else:
                ajax_response['response'] = error[1]

            ajax_response['rc'] = 1

            return HttpResponse(json.dumps(ajax_response))
        except:
            ajax_response['response'] = 'Unknown error.'
            return HttpResponse(json.dumps(ajax_response))

    # Del action
    if user_action == 'del':
        if request.REQUEST.get('id'):
            try:
                env = env_groups.get(id=request.REQUEST['id'])
                manager_id = env.manager_id
                if request.user.id != manager_id:
                    if not has_perm('management.delete_tcmsenvgroup'):
                        ajax_response['response'] = 'Permission denied.'
                        return HttpResponse(json.dumps(ajax_response))

                env.delete()
                ajax_response['response'] = 'ok'
            except TCMSEnvGroup.DoesNotExist, error:
                raise Http404(error)

            try:
                env_group_property_map = env_groups.filter(
                    group_id=request.REQUEST['id']
                )
                env_group_property_map.delete()
            except:
                pass
            return HttpResponse(json.dumps(ajax_response))
        else:
            pass

        if not has_perm('management.delete_tcmsenvgroup'):
            ajax_response['response'] = 'Permission denied.'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

    # Modify actions
    if user_action == 'modify':
        if not has_perm('management.change_tcmsenvgroup'):
            ajax_response['response'] = 'Permission denied.'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        try:
            env = env_groups.get(id=request.REQUEST['id'])
            if request.REQUEST.get('status') in ['0', '1']:
                env.is_active = int(request.REQUEST['status'])
                action = 'Change env group status to %s' % env.is_active
                env.log_action(who=request.user, action=action)
            else:
                ajax_response['response'] = 'Argument illegel.'
                ajax_response['rc'] = 1
                return HttpResponse(json.dumps(ajax_response))
            env.save()
        except TCMSEnvGroup.DoesNotExist, error:
            raise Http404(error)

    # Search actions
    if user_action == 'search':
        if request.REQUEST.get('name'):
            env_groups = env_groups.filter(
                name__icontains=request.REQUEST['name']
            )
        else:
            env_groups = env_groups.all()
    else:
        env_groups = env_groups.all().order_by('is_active')

    # Get properties for each group
    qs = TCMSEnvGroupPropertyMap.objects.filter(group__in=env_groups)
    qs = qs.values('group__pk', 'property__name')
    qs = qs.order_by('group__pk', 'property__name').iterator()
    properties = dict([(key, list(value)) for key, value in
                       groupby(qs, lambda item: item['group__pk'])])

    # Get logs for each group
    env_group_ct = ContentType.objects.get_for_model(TCMSEnvGroup)
    qs = TCMSLogModel.objects.filter(content_type=env_group_ct,
                                     object_pk__in=env_groups)
    qs = qs.values('object_pk', 'who__username', 'date', 'action')
    qs = qs.order_by('object_pk').iterator()
    # we have to convert object_pk to an integer due to it's a string stored in
    # database.
    logs = dict([(int(key), list(value)) for key, value in
                 groupby(qs, lambda log: log['object_pk'])])

    env_groups = env_groups.select_related('modified_by', 'manager').iterator()

    env_groups = QuerySetIterationProxy(env_groups,
                                        properties=properties,
                                        another_logs=logs)
    context_data = {
        'environments': env_groups,
        'module': 'env',
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('management.change_tcmsenvgroup'))
def environment_group_edit(request,
                           template_name='environment/group_edit.html'):
    """
    Assign properties to environment group
    """

    # Initial the response
    response = ''
    environment_id = request.REQUEST.get('id', None)

    if environment_id is None:
        raise Http404

    try:
        environment = TCMSEnvGroup.objects.get(pk=environment_id)
    except TCMSEnvGroup.DoesNotExist:
        raise Http404

    try:
        de = TCMSEnvGroup.objects.get(name=request.REQUEST.get('name'))
        if environment != de:
            response = 'Duplicated name already exists, please change to ' \
                'another name.'
            context_data = {
                'environment': environment,
                'properties': TCMSEnvProperty.get_active(),
                'selected_properties': environment.property.all(),
                'message': response,
            }
            return render_to_response(template_name, context_data,
                                      context_instance=RequestContext(request))
    except TCMSEnvGroup.DoesNotExist:
        pass

    if request.REQUEST.get('action') == 'modify':   # Actions of modify
        environment_name = request.REQUEST['name']
        if environment.name != environment_name:
            environment.name = environment_name
            environment.log_action(
                who=request.user,
                action='Modify name %s from to %s' % (environment.name,
                                                      environment_name))

        if environment.is_active != request.REQUEST.get('enabled', False):
            environment.is_active = request.REQUEST.get('enabled', False)
            environment.log_action(
                who=request.user,
                action='Change env group status to %s' % environment.is_active)

        environment.modified_by_id = request.user.id
        environment.save()

        # Remove all of properties of the group.
        TCMSEnvGroupPropertyMap.objects.filter(
            group__id=environment.id).delete()

        # Readd the property to environemnt group and log the action
        for property_id in request.REQUEST.getlist('selected_property_ids'):
            TCMSEnvGroupPropertyMap.objects.create(group_id=environment.id,
                                                   property_id=property_id)

        property_values = environment.property.values_list('name', flat=True)
        environment.log_action(
            who=request.user,
            action='Properties changed to %s' % (', '.join(property_values)))

        response = 'Environment group saved successfully.'

    context_data = {
        'environment': environment,
        'properties': TCMSEnvProperty.get_active(),
        'selected_properties': environment.property.all(),
        'message': response,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def environment_properties(request, template_name='environment/property.html'):
    """
    Edit environemnt properties and values belong to
    """

    # Initial the ajax response
    ajax_response = {'rc': 0, 'response': 'ok'}
    message = ''

    has_perm = request.user.has_perm
    user_action = request.REQUEST.get('action')

    # Actions of create properties
    if user_action == 'add':
        if not has_perm('management.add_tcmsenvproperty'):
            ajax_response['response'] = 'Permission denied'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        property_name = request.REQUEST.get('name')

        if not property_name:
            ajax_response['response'] = 'Property name is required'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        try:
            new_property = TCMSEnvProperty.objects.create(name=property_name)
            ajax_response['id'] = new_property.id
            ajax_response['name'] = new_property.name

        except IntegrityError, error:
            if error[1].startswith('Duplicate'):
                resp_msg = 'Environment proprerty named \'%s\' already ' \
                    'exists, please select another name.' % property_name
            else:
                resp_msg = error[1]

            ajax_response['rc'] = 1
            ajax_response['response'] = resp_msg
            return HttpResponse(json.dumps(ajax_response))

        return HttpResponse(json.dumps(ajax_response))

    # Actions of edit a exist properties
    if user_action == 'edit':
        if not has_perm('management.change_tcmsenvproperty'):
            ajax_response['response'] = 'Permission denied'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        if not request.REQUEST.get('id'):
            ajax_response['response'] = 'ID is required'
            ajax_response['rc'] = 1
            return HttpResponse(json.dumps(ajax_response))

        try:
            env_property = TCMSEnvProperty.objects.get(
                id=request.REQUEST['id'])
            env_property.name = request.REQUEST.get('name', env_property.name)
            try:
                env_property.save()
            except IntegrityError, error:
                ajax_response['response'] = error[1]
                ajax_response['rc'] = 1
                return HttpResponse(json.dumps(ajax_response))

        except TCMSEnvProperty.DoesNotExist, error:
            ajax_response['response'] = error[1]
            ajax_response['rc'] = 1

        return HttpResponse(json.dumps(ajax_response))

    # Actions of remove properties
    if user_action == 'del':
        if not has_perm('management.delete_tcmsenvproperty'):
            message = 'Permission denied'

        property_ids = request.REQUEST.getlist('id')

        if has_perm('management.delete_tcmsenvproperty') and property_ids:
            try:
                filter = TCMSEnvGroupPropertyMap.objects.filter

                env_group_property_map = filter(property__id__in=property_ids)
                env_group_property_map and env_group_property_map.delete()

                env_group_value_map = filter(property__id__in=property_ids)
                env_group_value_map and env_group_value_map.delete()
            except:
                pass

            try:
                env_properties = TCMSEnvProperty.objects.filter(
                    id__in=property_ids)
                property_values = '\', \''.join(
                    env_properties.values_list('name', flat=True))
                message = 'Remove test properties %s successfully.' % \
                    property_values
                env_properties.delete()
            except TCMSEnvProperty.DoesNotExist as error:
                message = error[1]

    # Actions of remove properties
    if user_action == 'modify':
        if not has_perm('management.change_tcmsenvproperty'):
            message = 'Permission denied'

        property_ids = request.REQUEST.getlist('id')

        if has_perm('management.change_tcmsenvproperty') and property_ids:
            try:
                env_properties = TCMSEnvProperty.objects.filter(
                    id__in=property_ids)

                if request.REQUEST.get('status') in ['0', '1']:
                    for env_property in env_properties:
                        env_property.is_active = int(request.REQUEST['status'])
                        env_property.save()

                    property_values = '\', \''.join(
                        env_properties.values_list('name', flat=True))
                    message = 'Modify test properties status \'%s\' ' \
                              'successfully.' % property_values
                else:
                    message = 'Argument illegel'

            except TCMSEnvProperty.DoesNotExist as error:
                message = error[1]

            try:
                filter = TCMSEnvGroupPropertyMap.objects.filter

                env_group_property_map = filter(property__id__in=property_ids)
                env_group_property_map and env_group_property_map.delete()

                env_group_value_map = filter(property__id__in=property_ids)
                env_group_value_map and env_group_value_map.delete()
            except:
                pass

    if request.is_ajax():
        ajax_response['rc'] = 1
        ajax_response['response'] = 'Unknown action'
        return HttpResponse(json.dumps(ajax_response))

    context_data = {
        'message': message,
        'properties': TCMSEnvProperty.objects.all().order_by('-is_active')
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def environment_property_values(request):
    """
    List values of property
    """
    template_name = 'environment/ajax/property_values.html'
    message = ''
    duplicated_property_value = []

    if not request.REQUEST.get('property_id'):
        return HttpResponse('Property ID should specify')

    try:
        qs = TCMSEnvProperty.objects.select_related('value')
        property = qs.get(id=request.REQUEST['property_id'])
    except TCMSEnvProperty.DoesNotExist, error:
        return HttpResponse(error)

    user_action = request.REQUEST.get('action')

    if user_action == 'add' and request.REQUEST.get('value'):
        if not request.user.has_perm('management.add_tcmsenvvalue'):
            return HttpResponse('Permission denied')

        for value in request.REQUEST['value'].split(','):
            try:
                property.value.create(value=value)
            except IntegrityError, error:
                if error[1].startswith('Duplicate'):
                    duplicated_property_value.append(value)

    if user_action == 'edit' and request.REQUEST.get('id'):
        if not request.user.has_perm('management.change_tcmsenvvalue'):
            return HttpResponse('Permission denied')

        try:
            property_value = property.value.get(id=request.REQUEST['id'])
            property_value.value = request.REQUEST.get('value',
                                                       property_value.value)
            try:
                property_value.save()
            except IntegrityError, error:
                if error[1].startswith('Duplicate'):
                    duplicated_property_value.append(property_value.value)

        except TCMSEnvValue.DoesNotExist, error:
            return HttpResponse(error[1])

    if user_action == 'modify' and request.REQUEST.get('id'):
        if not request.user.has_perm('management.change_tcmsenvvalue'):
            return HttpResponse('Permission denied')

        values = property.value.filter(id__in=request.REQUEST.getlist('id'))
        if request.REQUEST.get('status') in ['0', '1']:
            for value in values:
                value.is_active = int(request.REQUEST['status'])
                value.save()
        else:
            return HttpResponse('Argument illegel')

    if duplicated_property_value:
        message = 'Value(s) named \'%s\' already exists in this property, ' \
                  'please select another name.' % '\', \''.join(
                      duplicated_property_value)

    values = property.value.all()
    context_data = {
        'property': property,
        'values': values,
        'message': message,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))
