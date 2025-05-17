from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required


from .models import Company, UserProfile
from .forms import CompanyForm


class CompanyListView(LoginRequiredMixin, ListView):
    model = Company
    template_name = 'company/company_list.html'
    context_object_name = 'companies'

    def get_queryset(self):
        # Sprawdzamy, czy użytkownik ma profil
        try:
            # Firmy powiązane z profilem użytkownika
            return self.request.user.userprofile.company.all().order_by('name')
        except UserProfile.DoesNotExist:
            # Jeśli użytkownik nie ma profilu, tworzymy go
            UserProfile.objects.create(user=self.request.user)
            # Zwracamy pustą listę firm (nowy profil nie ma jeszcze firm)
            return Company.objects.none()


class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company/company_create_update.html'
    success_url = reverse_lazy('company:company_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj nową firmę'
        context['button_text'] = 'Dodaj firmę'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # Po zapisaniu firmy, powiąż ją z profilem użytkownika
        try:
            profile = self.request.user.userprofile
        except UserProfile.DoesNotExist:
            # Jeśli profil nie istnieje, utwórz go
            profile = UserProfile.objects.create(user=self.request.user)

        # Dodaj firmę do profilu
        profile.company.add(self.object)

        # Jeśli nie ma jeszcze aktywnej/domyślnej firmy, ustaw tę
        if not profile.active_company:
            profile.active_company = self.object
            profile.default_company = self.object
            profile.save()

        messages.success(
            self.request, f"Firma {form.instance.name} została dodana.")
        return response


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company/company_create_update.html'
    success_url = reverse_lazy('company:company_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj firmę: {self.object.name}'
        context['button_text'] = 'Zapisz zmiany'
        return context

    def form_valid(self, form):
        messages.success(
            self.request, f"Firma {form.instance.name} została zaktualizowana.")
        return super().form_valid(form)


class CompanyDeleteView(LoginRequiredMixin, DeleteView):
    model = Company
    template_name = 'company/company_delete_confirm.html'
    success_url = reverse_lazy('company:company_list')

    def delete(self, request, *args, **kwargs):
        company = self.get_object()
        messages.success(request, f"Firma {company.name} została usunięta.")
        return super().delete(request, *args, **kwargs)


# Przybliżona implementacja funkcji choose_company w apps/core/views.py

@login_required
def choose_company(request):
    """
    Widok umożliwiający użytkownikowi wybór aktywnej firmy.
    """
    # Dodajmy logging do debugowania
    import logging
    logger = logging.getLogger('django')
    logger.info(
        f"choose_company called with method: {request.method}, path: {request.path}")

    # Sprawdź i pobierz profil użytkownika
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # Jeśli profil nie istnieje, utwórz go
        logger.info(
            f"Tworzenie nowego profilu dla użytkownika: {request.user}")
        profile = UserProfile.objects.create(user=request.user)

    # Pobierz listę firm użytkownika
    companies = profile.company.all().order_by('name')
    logger.info(
        f"Znalezione firmy dla użytkownika {request.user}: {companies.count()}")

    # Sprawdź czy użytkownik jest administratorem (może korzystać z trybu master)
    show_master_option = request.user.is_staff or request.user.is_superuser

    # Obsługa żądania POST (gdy użytkownik wybiera firmę)
    if request.method == 'POST' and 'company_id' in request.POST:
        company_id = request.POST.get('company_id')
        logger.info(f"Otrzymano company_id: {company_id}")

        # Tryb administratora
        if company_id == 'master' and show_master_option:
            logger.info("Włączanie trybu administratora")
            profile.active_company = None
            profile.save()
            messages.success(
                request, "Włączono tryb administratora (dostęp do wszystkich firm).")
            return redirect('dashboard')

        # Wybrana konkretna firma
        try:
            company_id = int(company_id)
            company = get_object_or_404(Company, id=company_id)
            logger.info(f"Znaleziono firmę: {company}")

            # Sprawdź czy użytkownik ma dostęp do tej firmy
            if company in companies:
                logger.info(f"Ustawianie aktywnej firmy: {company}")
                profile.active_company = company
                profile.save()
                messages.success(
                    request, f"Firma {company.name} została ustawiona jako aktywna.")
                return redirect('dashboard')
            else:
                logger.warning(
                    f"Użytkownik {request.user} próbował ustawić firmę {company} do której nie ma dostępu")
                messages.error(request, "Nie masz dostępu do wybranej firmy.")
        except (ValueError, Company.DoesNotExist):
            logger.warning(f"Nieprawidłowy company_id: {company_id}")
            messages.error(request, "Wybrana firma nie istnieje.")

    # Automatycznie wybierz firmę, jeśli użytkownik ma tylko jedną
    if not profile.active_company and companies.count() == 1:
        logger.info(
            f"Automatyczny wybór jedynej firmy dla użytkownika {request.user}")
        profile.active_company = companies.first()
        profile.save()
        messages.success(
            request, f"Firma {profile.active_company.name} została automatycznie ustawiona jako aktywna.")
        return redirect('dashboard')

    logger.info("Renderowanie szablonu choose_company.html")
    return render(request, 'choose_company.html', {
        'companies': companies,
        'show_master_option': show_master_option
    })
