from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.company.models import Company

# Create your views here.
# views.py


def home_view(request):
    return render(request, 'home.html')


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
