# -*- coding: utf-8 -*-

from distutils.util import strtobool
from json import dumps as json_dumps
from itertools import groupby

from django.db import IntegrityError

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET

from tcms.core.logs.models import TCMSLogModel
from tcms.core.utils import QuerySetIterationProxy
from tcms.management.models import EnvGroup
from tcms.management.models import EnvGroupPropertyMap
from tcms.management.models import EnvProperty
from tcms.management.models import EnvValue


@require_GET
def environment_groups(request):
    """
    Environements list
    """

    has_perm = request.user.has_perm
    user_action = request.GET.get('action')

    # Add action
    if user_action == 'add':
        if not has_perm('management.add_envgroup'):
            return JsonResponse({'rc': 1, 'response': 'Permission denied.'})

        group_name = request.GET.get('name')

        # Get the group name of environment from javascript
        if not group_name:
            return JsonResponse({'rc': 1, 'response': 'Environment group name is required.'})

        if EnvGroup.objects.filter(name=group_name).exists():
            response_msg = "Environment group name '%s' already " \
                           'exists, please select another name.' % group_name
            return JsonResponse({'rc': 1, 'response': response_msg})

        env = EnvGroup.objects.create(name=group_name, manager_id=request.user.id,
                                      modified_by_id=None)
        env.log_action(who=request.user, action='Initial env group %s' % env.name)

        return JsonResponse({'rc': 0, 'response': 'ok', 'id': env.id})

    # Del action
    if user_action == 'del':
        if not request.GET.get('id'):
            raise Http404

        try:
            env_group_pk = int(request.GET['id'])
            env_group = get_object_or_404(EnvGroup, pk=env_group_pk)
        except ValueError:
            return JsonResponse({'rc': 1, 'response': 'id must be an integer.'})

        if request.user.pk != env_group.manager_id and not has_perm('management.delete_envgroup'):
                return JsonResponse({'rc': 1, 'response': 'Permission denied.'})

        env_group.delete()

        return JsonResponse({'rc': 0, 'response': 'ok'})

    # Modify actions
    if user_action == 'modify':
        if not has_perm('management.change_envgroup'):
            return JsonResponse({'rc': 1, 'response': 'Permission denied.'})

        try:
            env = EnvGroup.objects.get(id=request.GET['id'])
            if request.GET.get('status') in ['0', '1']:
                env.is_active = int(request.GET['status'])
                env.save(update_fields=['is_active'])

                action = 'Change env group status to {}'.format(env.is_active)
                env.log_action(who=request.user, action=action)
            else:
                return JsonResponse({'rc': 1, 'response': 'Argument illegal.'})
        except EnvGroup.DoesNotExist as error:
            raise Http404(error)

    # Search actions
    if user_action == 'search':
        if request.GET.get('name'):
            env_groups = EnvGroup.objects.filter(
                name__icontains=request.GET['name']
            )
        else:
            env_groups = EnvGroup.objects.all()
    else:
        env_groups = EnvGroup.objects.all().order_by('is_active')

    # Get properties for each group
    query_set = EnvGroupPropertyMap.objects.filter(group__in=env_groups).values(
        'group__pk', 'property__name').order_by(
        'group__pk', 'property__name').iterator()

    properties = {}
    for key, value in groupby(query_set, lambda item: item['group__pk']):
        properties[key] = list(value)

    # Get logs for each group
    env_group_content_type = ContentType.objects.get_for_model(EnvGroup)
    query_set = TCMSLogModel.objects.filter(
        content_type=env_group_content_type,
        object_pk__in=env_groups
    ).values('object_pk', 'who__username', 'date', 'action').order_by('object_pk').iterator()

    logs = {}
    for object_pk, value in groupby(query_set, lambda log: log['object_pk']):
        # we have to convert object_pk to an integer because it is a string, stored in the database
        logs[int(object_pk)] = list(value)

    env_groups = env_groups.select_related('modified_by', 'manager').iterator()

    env_groups = QuerySetIterationProxy(env_groups,
                                        properties=properties,
                                        another_logs=logs)
    context_data = {
        'environments': env_groups,
    }
    return render(request, 'environment/groups.html', context_data)


@require_GET
@permission_required('management.change_envgroup')
def environment_group_edit(request):
    """
    Assign properties to environment group
    """

    # Initial the response
    env_group_id = request.GET.get('id', None)
    env_group = get_object_or_404(EnvGroup, pk=env_group_id)

    try:
        env_group_with_same_name = EnvGroup.objects.get(name=request.GET.get('name'))
        if env_group != env_group_with_same_name:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Environment group with the same name already exists'))
            return HttpResponseRedirect(
                reverse('mgmt-environment_group_edit') + '?id=%s' % env_group_id)
    except EnvGroup.DoesNotExist:
        pass

    if request.GET.get('action') == 'modify':   # Actions of modify
        environment_name = request.GET['name']
        if env_group.name != environment_name:
            env_group.name = environment_name
            env_group.log_action(
                who=request.user,
                action='Modify name %s from to %s' % (env_group.name,
                                                      environment_name))

        if env_group.is_active != request.GET.get('enabled', False):
            env_group.is_active = strtobool(request.GET.get('enabled', False))
            env_group.log_action(
                who=request.user,
                action='Change env group status to %s' % env_group.is_active)

        env_group.modified_by_id = request.user.id
        env_group.save()

        # Remove all of properties of the group.
        EnvGroupPropertyMap.objects.filter(group__id=env_group.id).delete()

        # Readd the property to environemnt group and log the action
        for property_id in request.GET.getlist('selected_property_ids'):
            EnvGroupPropertyMap.objects.create(group_id=env_group.id, property_id=property_id)

        property_values = env_group.property.values_list('name', flat=True)
        env_group.log_action(
            who=request.user,
            action='Properties changed to %s' % (', '.join(property_values)))
        return HttpResponseRedirect(reverse('mgmt-environment_groups'))

    context_data = {
        'environment': env_group,
        'properties': EnvProperty.get_active(),
        'selected_properties': env_group.property.all(),
    }
    return render(request, 'environment/group_edit.html', context_data)


@require_GET
def environment_properties(request, template_name='environment/property.html'):
    """
    Edit environemnt properties and values belong to
    """

    # Initial the ajax response
    ajax_response = {'rc': 0, 'response': 'ok'}
    message = ''

    has_perm = request.user.has_perm
    user_action = request.GET.get('action')

    # Actions of create properties
    if user_action == 'add':
        if not has_perm('management.add_envproperty'):
            return JsonResponse({'rc': 1, 'response': 'Permission denied'})

        property_name = request.GET.get('name')

        if not property_name:
            return JsonResponse({'rc': 1, 'response': 'Property name is required'})

        if EnvProperty.objects.filter(name=property_name).exists():
            resp_msg = "Environment property named '{}' already exists, " \
                       "please select another name.".format(property_name)
            return JsonResponse({'rc': 1, 'response': resp_msg})

        new_property = EnvProperty.objects.create(name=property_name)

        return JsonResponse({
            'rc': 0,
            'response': 'ok',
            'id': new_property.pk,
            'name': new_property.name
        })

    # Actions of edit a exist properties
    if user_action == 'edit':
        if not has_perm('management.change_envproperty'):
            return JsonResponse({'rc': 1, 'response': 'Permission denied'})

        if not request.GET.get('id'):
            return JsonResponse({'rc': 1, 'response': 'ID is required'})

        try:
            property_id = request.GET['id']
            env_property = EnvProperty.objects.get(id=int(property_id))
        except ValueError:
            return JsonResponse({
                'rc': 1,
                'response': 'ID {} is not a valid integer.'.format(property_id)
            })
        except EnvProperty.DoesNotExist:
            return JsonResponse({'rc': 1, 'response': 'ID does not exist.'})

        new_name = request.GET.get('name', env_property.name)
        env_property.name = new_name
        try:
            env_property.save(update_fields=['name'])
        except Exception:
            return JsonResponse({'rc': 1, 'response': 'Cannot save property.'})

        return JsonResponse({'rc': 0, 'response': 'ok'})

    # Actions of remove properties
    if user_action == 'modify':
        if not has_perm('management.change_envproperty'):
            message = 'Permission denied'

        property_ids = request.GET.getlist('id')

        if has_perm('management.change_envproperty') and property_ids:
            env_properties = EnvProperty.objects.filter(id__in=property_ids)

            if request.GET.get('status') in ['0', '1']:
                for env_property in env_properties:
                    env_property.is_active = int(request.GET['status'])
                    env_property.save()

                property_values = "', '".join(env_properties.values_list('name', flat=True))
                message = "Modify test properties status '%s' successfully." % property_values

                if not env_property.is_active:
                    EnvGroupPropertyMap.objects.filter(
                        property__id__in=property_ids).delete()
            else:
                message = 'Argument illegal'

    if request.is_ajax():
        ajax_response['rc'] = 1
        ajax_response['response'] = 'Unknown action'
        return HttpResponse(json_dumps(ajax_response))

    context_data = {
        'message': message,
        'properties': EnvProperty.objects.all().order_by('-is_active')
    }
    return render(request, template_name, context_data)


@require_GET
def environment_property_values(request):
    """
    List values of property
    """
    duplicated_property_value = []

    if not request.GET.get('property_id'):
        return HttpResponse('Property ID should specify')

    env_property = get_object_or_404(EnvProperty, id=request.GET['property_id'])
    user_action = request.GET.get('action')

    if user_action == 'add' and request.GET.get('value'):
        if not request.user.has_perm('management.add_envvalue'):
            return HttpResponse('Permission denied')

        for value in request.GET['value'].split(','):
            try:
                env_property.value.create(value=value)
            except IntegrityError as error:
                if error[1].startswith('Duplicate'):
                    duplicated_property_value.append(value)

    if user_action == 'edit' and request.GET.get('id'):
        if not request.user.has_perm('management.change_envvalue'):
            return HttpResponse('Permission denied')

        try:
            property_value = env_property.value.get(id=request.GET['id'])
            property_value.value = request.GET.get('value', property_value.value)
            property_value.save()
        except EnvValue.DoesNotExist as error:
            return HttpResponse(error[1])
        except IntegrityError as error:
            if error[1].startswith('Duplicate'):
                duplicated_property_value.append(property_value.value)

    if user_action == 'modify' and request.GET.get('id'):
        if not request.user.has_perm('management.change_envvalue'):
            return HttpResponse('Permission denied')

        values = env_property.value.filter(id__in=request.GET.getlist('id'))
        status = request.GET.get('status')
        if status in ['0', '1']:
            for value in values:
                value.is_active = int(status)
                value.save()
        else:
            return HttpResponse('Argument illegal')

    message = ''
    if duplicated_property_value:
        message = _("Value(s) named '%s' already exists in this property. "
                    "Please select another name.") % ', '.join(duplicated_property_value)

    values = env_property.value.all()
    context_data = {
        'property': env_property,
        'values': values,
        'message': message,
    }
    return render(request, 'environment/ajax/property_values.html', context_data)
