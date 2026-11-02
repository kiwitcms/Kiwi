from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.urls import reverse # Added for the cancel redirect

from tcms.management.models import Product, Component, Version, Build
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from ..forms import ProjectForm, ComponentForm

@login_required
def project_settings(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'tcms_ui_custom/project_settings.html', {'products': products})

@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Project created successfully!")
            return redirect('project_settings')
    else:
        form = ProjectForm()
    return render(request, 'tcms_ui_custom/project_form.html', {'form': form, 'action': 'Create', 'cancel_url': reverse('project_settings')})

@login_required
def project_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Handle the Cancel redirect logic
    if request.GET.get('next') == 'overview':
        cancel_url = reverse('project_overview', args=[product.pk])
    else:
        cancel_url = reverse('project_settings')

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully!")
            return redirect(cancel_url)
    else:
        form = ProjectForm(instance=product)

    return render(request, 'tcms_ui_custom/project_form.html', {
        'form': form,
        'action': 'Edit',
        'cancel_url': cancel_url
    })

@login_required
def project_overview(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form_has_error = False

    if request.method == 'POST' and 'add_module' in request.POST:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not description:
            messages.error(request, "Both Module Name and Description are required.")
            form_has_error = True
        else:
            Component.objects.create(product=product, name=name, description=description)
            messages.success(request, f"Module '{name}' created successfully.")
            return redirect('project_overview', pk=product.pk)

    components = Component.objects.filter(product=product).order_by('name')
    testcases = TestCase.objects.filter(component__product_id=product.pk).distinct().order_by('-id')
    versions = Version.objects.filter(product=product).order_by('-id')
    builds = Build.objects.filter(version__product=product).order_by('-id')
    testplans = TestPlan.objects.filter(product=product, is_active=True).order_by('-id')

    return render(request, 'tcms_ui_custom/project_overview.html', {
        'product': product,
        'components': components,
        'testcases': testcases,
        'versions': versions,
        'builds': builds,
        'testplans': testplans,
        'form_has_error': form_has_error
    })

@login_required
def component_edit(request, pk):
    component = get_object_or_404(Component, pk=pk)
    if request.method == 'POST':
        form = ComponentForm(request.POST, instance=component)
        if form.is_valid():
            form.save()
            messages.success(request, "Module updated successfully!")
            return redirect('project_overview', pk=component.product.pk)
    else:
        form = ComponentForm(instance=component)
    return render(request, 'tcms_ui_custom/component_form.html', {'form': form, 'component': component})

@login_required
def component_delete(request, pk):
    component = get_object_or_404(Component, pk=pk)
    product_id = component.product.pk

    if request.method == 'POST':
        try:
            component.delete()
            messages.success(request, "Module deleted.")
        except ProtectedError as e:
            messages.error(request, str(e))

    return redirect('project_overview', pk=product_id)

@login_required
def version_create(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        value = request.POST.get('value', '').strip()
        if value:
            try:
                Version.objects.create(product=product, value=value)
                messages.success(request, f"Version '{value}' added.")
            except IntegrityError:
                messages.error(request, f"Version '{value}' already exists for this project.")
        else:
            messages.error(request, "Version name cannot be empty.")
    return redirect('project_overview', pk=pk)

@login_required
def version_delete(request, pk, version_pk):
    version = get_object_or_404(Version, pk=version_pk, product_id=pk)
    if request.method == 'POST':
        try:
            version.delete()
            messages.success(request, f"Version '{version.value}' deleted.")
        except ProtectedError as e:
            messages.error(request, str(e))
    return redirect('project_overview', pk=pk)

@login_required
def build_create(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            version = Version.objects.filter(product=product).first()
            if version:
                Build.objects.create(version=version, name=name)
                messages.success(request, f"Build '{name}' added.")
            else:
                messages.error(request, "You must create at least one Version before adding a Build.")
        else:
            messages.error(request, "Build name cannot be empty.")
    return redirect('project_overview', pk=pk)

@login_required
def build_delete(request, pk, build_pk):
    build = get_object_or_404(Build, pk=build_pk, version__product_id=pk)
    if request.method == 'POST':
        try:
            build.delete()
            messages.success(request, f"Build '{build.name}' deleted.")
        except ProtectedError as e:
            messages.error(request, str(e))
    return redirect('project_overview', pk=pk)
