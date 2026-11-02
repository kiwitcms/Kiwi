import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction 

from tcms.testplans.models import TestPlan, PlanType
from tcms.testruns.models import TestRun, TestExecution, TestExecutionStatus 
from tcms.testcases.models import TestCase
from tcms.management.models import Product, Component, Tag, Version, Build
from ..models import TestPlanMetadata

# --- API VIEWS ---
@login_required
def api_get_testcases(request):
    component_ids = request.GET.getlist('components[]') or request.GET.getlist('components')
    if not component_ids:
        return JsonResponse({'cases': []})
    testcases = TestCase.objects.filter(component__id__in=component_ids).distinct().values('id', 'summary', 'component__name')
    return JsonResponse({'cases': list(testcases)})

@login_required
def api_get_modules(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'modules': []})
    components = Component.objects.filter(product_id=product_id).order_by('name').values('id', 'name')
    return JsonResponse({'modules': list(components)})

@login_required
def api_get_versions(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'versions': []})
    versions = Version.objects.filter(product_id=product_id).order_by('-id').values('id', 'value')
    return JsonResponse({'versions': list(versions)})

# --- MAIN VIEWS ---
@login_required
def testplan_list(request):
    testplans = TestPlan.objects.filter(is_active=True).order_by('-id')
    return render(request, 'tcms_ui_custom/testplans/testplan_list.html', {'testplans': testplans})

@login_required
def testplan_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        product_id = request.POST.get('product')
        version_id = request.POST.get('product_version')
        
        if not name or not product_id or not version_id:
            messages.error(request, "Name, Project, and Version are required.")
        else:
            try:
                with transaction.atomic():
                    product = get_object_or_404(Product, pk=product_id)
                    product_version = get_object_or_404(Version, pk=version_id)
                    
                    plan_type = PlanType.objects.first() or PlanType.objects.create(name='Default')

                    plan = TestPlan.objects.create(
                        name=name, product=product, product_version=product_version, 
                        type=plan_type, author=request.user
                    )
                    
                    metadata = TestPlanMetadata.objects.create(
                        testplan=plan,
                        description=request.POST.get('description'),
                        environment=request.POST.get('environment'),
                        target_date=request.POST.get('target_date') or None
                    )
                    
                    if request.POST.getlist('resources[]'):
                        metadata.resources.set(request.POST.getlist('resources[]'))
                    
                    in_scope_cases = TestCase.objects.filter(id__in=request.POST.getlist('in_scope_cases[]'))
                    plan.cases.add(*in_scope_cases)
                    
                    if request.POST.getlist('out_scope_cases[]'):
                        metadata.out_of_scope_cases.set(TestCase.objects.filter(id__in=request.POST.getlist('out_scope_cases[]')))

                    product_build = Build.objects.filter(version__product=product).first()
                    if not product_build:
                        product_build = Build.objects.create(version=product_version, name='Default Build')

                    default_status = TestExecutionStatus.objects.first()
                    if not default_status:
                        default_status = TestExecutionStatus.objects.create(name='IDLE', is_default=True)

                    strategies = Tag.objects.filter(id__in=request.POST.getlist('strategies[]'))
                    runs_count = 0
                    for strategy in strategies:
                        run = TestRun.objects.create(
                            summary=f"{plan.name} - {strategy.name}",
                            plan=plan, build=product_build, manager=request.user,
                            notes=f"Auto-generated run for strategy {strategy.name}"
                        )
                        cases_for_run = in_scope_cases.filter(tag=strategy)
                        for case in cases_for_run:
                            TestExecution.objects.create(
                                run=run, case=case, build=product_build,      
                                status=default_status, case_text_version=1,
                                assignee=request.user, sortkey=0
                            )
                        runs_count += 1

                messages.success(request, f"Test Plan '{plan.name}' created, and {runs_count} Test Runs generated.")
                return redirect('testplan_list')
            except Exception as e:
                messages.error(request, f"Failed to create Test Plan: {str(e)}")

    selected_product_id = request.GET.get('product')
    versions = Version.objects.none()
    if selected_product_id:
        versions = Version.objects.filter(product_id=selected_product_id).order_by('-id')

    return render(request, 'tcms_ui_custom/testplans/testplan_form.html', {
        'products': Product.objects.all().order_by('name'),
        'users': User.objects.filter(is_active=True).order_by('username'),
        'strategies': Tag.objects.all().order_by('name'),
        'selected_product_id': selected_product_id,
        'versions': versions,
    })

@login_required
def testplan_detail(request, pk):
    plan = get_object_or_404(TestPlan, pk=pk)
    test_cases = TestCase.objects.filter(testcaseplan__plan=plan).order_by('id')
    runs = TestRun.objects.filter(plan=plan).order_by('-id')
    
    # Calculate completion status for each run
    runs_data = []
    for run in runs:
        untested = TestExecution.objects.filter(run=run, status__name='IDLE').count()
        runs_data.append({
            'run': run,
            'is_complete': (untested == 0)
        })
    
    if request.method == 'POST' and 'update_status' in request.POST:
        new_status = request.POST.get('status')
        if new_status in dict(TestPlanMetadata.STATUS_CHOICES):
            plan.custom_metadata.status = new_status
            plan.custom_metadata.save()
            messages.success(request, "Plan status updated.")
            return redirect('testplan_detail', pk=plan.pk)

    return render(request, 'tcms_ui_custom/testplans/testplan_detail.html', {
        'plan': plan, 
        'test_cases': test_cases,
        'runs_data': runs_data,
        'status_choices': TestPlanMetadata.STATUS_CHOICES
    })

@login_required
def testplan_toggle_active(request, pk):
    plan = get_object_or_404(TestPlan, pk=pk)
    if request.method == 'POST':
        plan.is_active = not plan.is_active
        plan.save()
        status_text = "enabled" if plan.is_active else "disabled"
        messages.success(request, f"Test Plan '{plan.name}' has been {status_text}.")
    return redirect(request.META.get('HTTP_REFERER', 'testplan_list'))