from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone  # Add this import

# Import your models
from apps.company.models import Company
from apps.partner.models import Partner
from apps.subscriber.models import Subscriber
# This is already imported in your code
from apps.product.models import Product
from django.contrib.auth import authenticate, login, logout

# apps/core/views.py (update or add this function)


def login_view(request):
    """Login view that handles authentication"""
    if request.user.is_authenticated:
        # If already logged in, redirect to home
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirect to the page they were trying to access or home
            next_url = request.POST.get(
                'next') or request.GET.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'login.html', {'hide_sidebar': True, 'hide_navbar': True})


@login_required
def home_view(request):
    """
    Home view that shows login page for anonymous users
    and dashboard for authenticated users
    """
    if request.user.is_authenticated:
        # User is logged in, get dashboard data
        context = {}

        # Count data for statistics
        context['partners_count'] = Partner.objects.count()
        context['subscribers_count'] = Subscriber.objects.count()
        context['products_count'] = Product.objects.count()
        context['verified_partners_count'] = Partner.objects.filter(
            is_verified=True).count()

        # Get recent activities (e.g., recently added partners)
        recent_partners = Partner.objects.order_by('-created_at')[:5]
        recent_subscribers = Subscriber.objects.order_by('-created_at')[:5]

        # Combine and sort by date
        activities = []

        for partner in recent_partners:
            activities.append({
                'title': f"Partner Added: {partner.name}",
                'description': f"VAT: {partner.get_full_vat_number()}",
                'date': partner.created_at,
                'type': 'partner'
            })

        for subscriber in recent_subscribers:
            activities.append({
                'title': f"Subscriber Added: {subscriber.email}",
                'description': f"Name: {subscriber.first_name} {subscriber.last_name}",
                'date': subscriber.created_at,
                'type': 'subscriber'
            })

        # Sort by date (newest first)
        activities.sort(key=lambda x: x['date'], reverse=True)

        # Take only the 10 most recent
        context['recent_activities'] = activities[:10]

        # Check if user has a company profile
        try:
            profile = request.user.userprofile
            context['user_companies'] = profile.company.all()
            context['active_company'] = profile.active_company
            context['default_company'] = profile.default_company
        except:
            context['user_companies'] = []
            context['active_company'] = None
            context['default_company'] = None

        # Show dashboard
        return render(request, 'dashboard.html', context)
    else:
        # User is not logged in, show login page
        return render(request, 'login.html')


@login_required
def choose_company(request):
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        # Sprawdź, czy użytkownik ma dostęp do tej firmy
        if company_id == 'master' and request.user.is_staff:
            # Specjalny przypadek dla widoku wszystkiego
            request.session['company_id'] = None
            request.session['is_master_view'] = True
        else:
            company = get_object_or_404(Company, id=company_id)
            # Tutaj możesz dodać logikę sprawdzającą uprawnienia
            request.session['company_id'] = company.id
            request.session['is_master_view'] = False

        return redirect('dashboard')

    # Pobierz firmy, do których użytkownik ma dostęp
    if request.user.is_staff:
        # pylint: disable=no-member
        companies = Company.objects.all()
        show_master_option = True
    else:
        # Załóżmy, że mamy relację M2M między User a Company
        companies = request.user.company.all()
        show_master_option = False

    return render(request, 'choose_company.html', {
        'companies': companies,
        'show_master_option': show_master_option
    })


@login_required
def products_list_view(request):
    """View for displaying a list of products"""
    return render(request, 'products-list.html')


@login_required
def newsletters_list_view(request):
    """View for displaying a list of newsletters"""
    return render(request, 'newsletters-list.html')


@login_required
def sales_offers_list_view(request):
    """View for displaying a list of sales offers"""
    return render(request, 'sales-offers-list.html')


def logout_view(request):
    """Custom logout view that explicitly redirects to login"""
    logout(request)
    # Use direct path instead of URL name to avoid any resolution issues
    return redirect('/login/')


@login_required
def dashboard_view(request):
    # Initialize context with default values
    context = {
        'partners_count': 0,
        'subscribers_count': 0,
        'products_count': 0,
        'verified_partners_count': 0,
        'recent_activities': []
    }

    # Try to get the counts, handle any errors
    try:
        from apps.partner.models import Partner
        context['partners_count'] = Partner.objects.all().count()
        try:
            context['verified_partners_count'] = Partner.objects.filter(
                is_verified=True).count()
        except:
            pass  # If is_verified field doesn't exist
    except:
        pass  # If Partner model doesn't exist

    try:
        from apps.subscriber.models import Subscriber
        context['subscribers_count'] = Subscriber.objects.all().count()
    except:
        pass  # If Subscriber model doesn't exist

    try:
        from apps.product.models import Product
        context['products_count'] = Product.objects.all().count()
    except:
        pass  # If Product model doesn't exist

    # Example recent activities
    context['recent_activities'] = [
        {
            'title': 'New Partner Added',
            'description': 'Partner "Acme Inc." was added to the system.',
            'date': '2 hours ago'
        },
        {
            'title': 'VAT Verification',
            'description': 'Partner "XYZ Corp" VAT was verified successfully.',
            'date': '4 hours ago'
        },
        {
            'title': 'New Subscriber',
            'description': 'New subscriber john.doe@example.com was added.',
            'date': '1 day ago'
        }
    ]

    return render(request, 'dashboard.html', context)
