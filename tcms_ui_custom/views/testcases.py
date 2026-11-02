import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from tcms.management.models import Priority, Tag, Component
from tcms.testcases.models import TestCase, Category, TestCaseStatus
from ..forms import TestCaseForm

def _format_testcase_text(form, request):
    desc = form.cleaned_data.get('description', '')
    pre = form.cleaned_data.get('pre_conditions', '')
    post = form.cleaned_data.get('post_conditions', '')
    
    steps = request.POST.getlist('step[]')
    expected = request.POST.getlist('expected[]')
    
    steps_html = "<table><thead><tr><th style='width: 50%;'>Step</th><th>Expected Result</th></tr></thead><tbody>"
    has_steps = False
    for s, e in zip(steps, expected):
        if s.strip() or e.strip():
            has_steps = True
            steps_html += f"<tr><td>{s}</td><td>{e}</td></tr>"
    steps_html += "</tbody></table>"

    formatted_text = ""
    if desc: formatted_text += f"<h5>Description</h5><p>{desc}</p><br>"
    if pre: formatted_text += f"<h5>Pre-conditions</h5><p>{pre}</p><br>"
    if post: formatted_text += f"<h5>Post-conditions</h5><p>{post}</p><br>"
    if has_steps: formatted_text += f"<h5>Steps</h5>{steps_html}"

    return formatted_text

@login_required
def testcase_list(request):
    component_id = request.GET.get('component')
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    testcases = TestCase.objects.all().order_by('-id')

    if component_id:
        testcases = testcases.filter(component__id=component_id)
    
    if query:
        testcases = testcases.filter(Q(summary__icontains=query) | Q(pk__icontains=query))
        
    if status_filter:
        testcases = testcases.filter(case_status__name=status_filter)

    # Pagination
    paginator = Paginator(testcases, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tcms_ui_custom/testcase_list.html', {
        'page_obj': page_obj,
        'testcases': page_obj.object_list,
        'selected_component': Component.objects.filter(pk=component_id).first() if component_id else None,
        'query': query,
        'status_filter': status_filter,
        'statuses': TestCaseStatus.objects.all(),
        'component_id': component_id,
    })

@login_required
def testcase_create(request):
    if request.method == 'POST':
        form = TestCaseForm(request.POST)
        if form.is_valid():
            component_obj = form.cleaned_data['component']
            testcase = form.save(commit=False)
            
            testcase.author = request.user
            testcase.default_tester = request.user
            testcase.priority = Priority.objects.first() or Priority.objects.create(value=1, is_active=True)
            testcase.case_status = form.cleaned_data['case_status']
            testcase.category = Category.objects.first() or Category.objects.create(name='Default', product=component_obj.product)

            testcase.text = _format_testcase_text(form, request)
            testcase.save()
            testcase.component.add(component_obj)
            
            for tag in form.cleaned_data['tags_input']:
                testcase.add_tag(tag)
                
            messages.success(request, "Test Case created successfully!")
            return redirect(f"/repository/?product={component_obj.product.pk}&component={component_obj.pk}")
    else:
        form = TestCaseForm()
        comp_id = request.GET.get('component')
        if comp_id:
            form.fields['component'].initial = comp_id

    return render(request, 'tcms_ui_custom/testcase_form.html', {'form': form, 'action': 'Create'})

@login_required
def testcase_view(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    return render(request, 'tcms_ui_custom/testcase_view.html', {'tc': testcase})

@login_required
def testcase_edit(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    if request.method == 'POST':
        form = TestCaseForm(request.POST, instance=testcase)
        if form.is_valid():
            tc = form.save(commit=False)
            tc.case_status = form.cleaned_data['case_status']
            tc.text = _format_testcase_text(form, request)
            tc.save()
            
            tc.component.clear()
            tc.component.add(form.cleaned_data['component'])
            
            tc.tag.clear()
            for tag in form.cleaned_data['tags_input']:
                tc.add_tag(tag)
                
            messages.success(request, "Test Case updated successfully!")
            return redirect('testcase_view', pk=tc.pk)
    else:
        text = testcase.text or ""
        desc_match = re.search(r'<h5>Description</h5><p>(.*?)</p>', text, re.DOTALL)
        pre_match = re.search(r'<h5>Pre-conditions</h5><p>(.*?)</p>', text, re.DOTALL)
        post_match = re.search(r'<h5>Post-conditions</h5><p>(.*?)</p>', text, re.DOTALL)
        steps = re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td></tr>', text)

        initial_data = {
            'description': desc_match.group(1) if desc_match else "",
            'pre_conditions': pre_match.group(1) if pre_match else "",
            'post_conditions': post_match.group(1) if post_match else "",
            'tags_input': testcase.tag.all(),
            'component': testcase.component.first(),
            'case_status': testcase.case_status,
        }
        form = TestCaseForm(instance=testcase, initial=initial_data)

        return render(request, 'tcms_ui_custom/testcase_form.html', {
            'form': form, 
            'action': 'Edit', 
            'tc': testcase,
            'existing_steps': steps
        })

    return render(request, 'tcms_ui_custom/testcase_form.html', {'form': form, 'action': 'Edit', 'tc': testcase})

@login_required
def testcase_delete(request, pk):
    testcase = get_object_or_404(TestCase, pk=pk)
    component_id = testcase.component.first().pk if testcase.component.exists() else None
    product_id = testcase.component.first().product.pk if testcase.component.exists() else None
    
    if request.method == 'POST':
        testcase.delete()
        messages.success(request, "Test Case deleted.")
        if component_id:
            return redirect(f"/repository/?product={product_id}&component={component_id}")
        return redirect('testcase_list')
        
    return render(request, 'tcms_ui_custom/testcase_confirm_delete.html', {'tc': testcase})