from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from tcms.management.models import Priority, Tag
from tcms.testcases.models import TestCaseStatus, TestCase, TestCaseTag

@login_required
def settings_index(request):
    return render(request, 'tcms_ui_custom/settings/index.html')

# --- PRIORITIES ---
@login_required
def settings_priorities(request):
    priorities = Priority.objects.all().order_by('value')
    priorities_in_use_ids = list(TestCase.objects.values_list('priority_id', flat=True).distinct())

    if request.method == 'POST':
        value = request.POST.get('value', '').strip()
        if value:
            Priority.objects.create(value=value, is_active=True)
            messages.success(request, f"Priority '{value}' added.")
            return redirect('settings_priorities')

    return render(request, 'tcms_ui_custom/settings/priorities.html', {
        'priorities': priorities,
        'priorities_in_use_ids': priorities_in_use_ids
    })

@login_required
def priority_edit(request, pk):
    priority = get_object_or_404(Priority, pk=pk)
    if request.method == 'POST':
        value = request.POST.get('value', '').strip()
        if value:
            priority.value = value
            priority.save()
            messages.success(request, "Priority updated.")
    return redirect('settings_priorities')

@login_required
def priority_delete(request, pk):
    priority = get_object_or_404(Priority, pk=pk)
    if request.method == 'POST':
        try:
            priority.delete()
            messages.success(request, "Priority deleted.")
        except ProtectedError as e:
            messages.error(request, str(e))
    return redirect('settings_priorities')

# --- STATUSES ---
@login_required
def settings_statuses(request):
    statuses = TestCaseStatus.objects.all().order_by('name')
    statuses_in_use_ids = list(TestCase.objects.values_list('case_status_id', flat=True).distinct())

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            TestCaseStatus.objects.create(name=name.upper())
            messages.success(request, f"Status '{name.upper()}' added.")
            return redirect('settings_statuses')

    return render(request, 'tcms_ui_custom/settings/statuses.html', {
        'statuses': statuses,
        'statuses_in_use_ids': statuses_in_use_ids
    })

@login_required
def status_edit(request, pk):
    status = get_object_or_404(TestCaseStatus, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            status.name = name.upper()
            status.save()
            messages.success(request, "Status updated.")
    return redirect('settings_statuses')

@login_required
def status_delete(request, pk):
    status = get_object_or_404(TestCaseStatus, pk=pk)
    if request.method == 'POST':
        try:
            status.delete()
            messages.success(request, "Status deleted.")
        except ProtectedError as e:
            messages.error(request, str(e))
    return redirect('settings_statuses')

# --- TAGS ---
@login_required
def settings_tags(request):
    tags = Tag.objects.all().order_by('name')
    tags_in_use_ids = list(TestCaseTag.objects.values_list('tag_id', flat=True).distinct())

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Tag.objects.create(name=name)
            messages.success(request, f"Tag '{name}' added.")
            return redirect('settings_tags')

    return render(request, 'tcms_ui_custom/settings/tags.html', {
        'tags': tags,
        'tags_in_use_ids': tags_in_use_ids
    })

@login_required
def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            tag.name = name
            tag.save()
            messages.success(request, "Tag updated.")
    return redirect('settings_tags')

@login_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == 'POST':
        try:
            tag.delete()
            messages.success(request, "Tag deleted.")
        except ProtectedError as e:
            messages.error(request, str(e))
    return redirect('settings_tags')
