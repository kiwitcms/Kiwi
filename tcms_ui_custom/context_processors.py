from tcms.management.models import Product

def jira_sidebar_products(request):
    if not request.user.is_authenticated:
        return {}

    # Now we use the correct reverse relationship name: 'component'
    products = Product.objects.prefetch_related('component').all().order_by('name')
    
    return {'jira_sidebar_products': products}