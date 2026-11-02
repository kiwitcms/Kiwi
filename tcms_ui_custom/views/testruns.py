from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tcms.testruns.models import TestRun, TestExecution, TestExecutionStatus
from tcms.testcases.models import TestCase

# Helper to ensure DEFERRED status exists
def get_deferred_status():
    status, _ = TestExecutionStatus.objects.get_or_create(name='DEFERRED', defaults={'is_default': False})
    return status

@login_required
def testrun_detail(request, pk):
    run = get_object_or_404(TestRun, pk=pk)
    executions = TestExecution.objects.filter(run=run).order_by('id')
    
    total = executions.count()
    passed = executions.filter(status__name='PASS').count()
    failed = executions.filter(status__name='FAIL').count()
    blocked = executions.filter(status__name='BLOCKED').count()
    deferred = executions.filter(status__name='DEFERRED').count()
    untested = total - (passed + failed + blocked + deferred)
    
    pass_pct = (passed / total * 100) if total > 0 else 0
    fail_pct = (failed / total * 100) if total > 0 else 0
    block_pct = (blocked / total * 100) if total > 0 else 0
    defer_pct = (deferred / total * 100) if total > 0 else 0
    untested_pct = (untested / total * 100) if total > 0 else 0

    modules_dict = {}
    for exe in executions:
        comp = exe.case.component.first()
        comp_name = comp.name if comp else "Unassigned"
        if comp_name not in modules_dict:
            modules_dict[comp_name] = []
        modules_dict[comp_name].append(exe)

    return render(request, 'tcms_ui_custom/testruns/testrun_detail.html', {
        'run': run,
        'modules_dict': modules_dict,
        'stats': {
            'total': total, 'passed': passed, 'failed': failed, 'blocked': blocked, 'deferred': deferred, 'untested': untested,
            'pass_pct': pass_pct, 'fail_pct': fail_pct, 'block_pct': block_pct, 'defer_pct': defer_pct, 'untested_pct': untested_pct,
            'is_complete': (untested == 0)
        }
    })

@login_required
def testrun_edit(request, pk):
    run = get_object_or_404(TestRun, pk=pk)
    executions = TestExecution.objects.filter(run=run).order_by('id')
    
    modules_dict = {}
    for exe in executions:
        comp = exe.case.component.first()
        comp_name = comp.name if comp else "Unassigned"
        if comp_name not in modules_dict:
            modules_dict[comp_name] = []
        modules_dict[comp_name].append(exe)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_executions[]')
        
        # Delete any executions for this run that were NOT selected
        deleted_count, _ = TestExecution.objects.filter(run=run).exclude(id__in=selected_ids).delete()
        messages.success(request, f"Run updated. {deleted_count} test cases removed.")
        return redirect('testplan_detail', pk=run.plan.pk)

    return render(request, 'tcms_ui_custom/testruns/testrun_edit.html', {
        'run': run,
        'modules_dict': modules_dict,
    })

@login_required
def execute_test(request, run_pk, case_pk):
    run = get_object_or_404(TestRun, pk=run_pk)
    testcase = get_object_or_404(TestCase, pk=case_pk)
    execution = get_object_or_404(TestExecution, run=run, case=testcase)
    
    if request.method == 'POST':
        status_name = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        status_obj = TestExecutionStatus.objects.filter(name=status_name).first()
        if not status_obj and status_name == 'DEFERRED':
            status_obj = get_deferred_status()
            
        if status_obj:
            execution.status = status_obj
            execution.notes = notes
            execution.save()
            messages.success(request, f"Test Case TC-{testcase.pk} marked as {status_name}.")
            
        action = request.POST.get('action')
        executions = list(TestExecution.objects.filter(run=run).order_by('id'))
        current_index = executions.index(execution)
        
        if action == 'next' and current_index < len(executions) - 1:
            return redirect('execute_test', run_pk=run.pk, case_pk=executions[current_index + 1].case.pk)
        elif action == 'prev' and current_index > 0:
            return redirect('execute_test', run_pk=run.pk, case_pk=executions[current_index - 1].case.pk)
            
        return redirect('testrun_detail', pk=run.pk)

    executions = list(TestExecution.objects.filter(run=run).order_by('id'))
    current_index = executions.index(execution)
    prev_case = executions[current_index - 1].case if current_index > 0 else None
    next_case = executions[current_index + 1].case if current_index < len(executions) - 1 else None

    return render(request, 'tcms_ui_custom/testruns/execute_test.html', {
        'run': run,
        'execution': execution,
        'testcase': testcase,
        'prev_case': prev_case,
        'next_case': next_case,
    })