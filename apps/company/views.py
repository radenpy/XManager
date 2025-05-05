
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Company, UserProfile


@login_required
def choose_company(request):
    # Pobieramy profil zalogowanego użytkownika
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        company_id = request.POST.get('company_id')

        if company_id == 'master':
            request.session['company_id'] = 'master'
            return redirect('dashboard:home')

        # Jeśli to nie master, próbujemy znaleźć firmę w bazie danych
        company = get_object_or_404(Company, id=company_id)
        request.session['company_id'] = company.id
        return redirect('dashboard:home')

    # Jeśli to GET, renderujemy stronę wyboru firmy
    return render(request, "companies/choose_company.html", {
        "companies": profile.company.all(),  # Lista firm przypisanych do profilu
        "current": profile.active_company,     # Aktualnie wybrana firma
        "default": profile.default_company,    # Domyślna firma użytkownika
    })
