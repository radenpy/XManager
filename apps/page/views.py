from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib.auth.decorators import login_required
# Upewnij się, że ścieżka jest prawidłowa
from apps.company.models import Company
from apps.product.models import Product


def home_view(request):
    return render(request, 'home.html')


def dashboard_view(request):
    return render(request, 'dashboard.html')


def products_list_view(request):
    return render(request, 'products-list.html')


def newsletters_list_view(request):
    return render(request, 'newsletters-list.html')


def sales_offers_list_view(request):
    return render(request, 'sales-offers-list.html')


def choose_context_view(request):
    return render(request, 'choose-context.html')


def login_view(request):
    pass


# # Jeśli użytkownik nie jest zalogowany, wyświetlamy stronę logowania
# if not request.user.is_authenticated:
#     return render(request, 'home.html')

# # Jeśli użytkownik jest zalogowany, ale nie wybrał firmy, przekierowujemy do choose_company
# if not request.session.get('company_id'):
#     return redirect('choose_company.html')

# # Jeśli firma jest wybrana, pokazujemy dashboard
# return render(request, 'dashboard.html')


# @login_required
# def choose_company(request):
#     # Jeśli to POST (wybranie firmy)
#     if request.method == 'POST':
#         company_id = request.POST.get('company_id')
#         if company_id == 'master':
#             request.session['company_id'] = 'master'
#         else:
#             try:
#                 # Próbujemy znaleźć firmę w bazie danych
#                 company = Company.objects.get(id=company_id)
#                 request.session['company_id'] = company.id
#             except Company.DoesNotExist:
#                 # Jeśli firma nie istnieje, przekieruj użytkownika z komunikatem
#                 return redirect('companies:choose-company')

#         # Przekierowanie do strony home (które teraz będzie działało dla wybranego kontekstu)
#         return redirect('dashboard:home')

#     # Jeśli to GET, wyświetlamy listę firm
#     return render(request, "companies/choose_company.html", {
#         "companies": Company.objects.all(),  # Lista wszystkich firm
#         # Pokazujemy aktualnie wybraną firmę
#         "current": request.session.get('company_id', 'brak'),
#     })
