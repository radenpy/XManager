from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django_countries import countries
from django.utils import timezone
from django.db.models import Q
import logging


from .models import Partner, PartnerEmail, VATVerificationHistory
from .forms import PartnerCreateForm, PartnerFilterForm
from .vat_service import VATService
from .utils import add_to_context

from apps.subscriber.models import Subscriber
from apps.core.vat_verification import VATVerificationService

logger = logging.getLogger(__name__)


class PartnerListView(LoginRequiredMixin, ListView):
    """Lista partnerów"""
    model = Partner
    template_name = 'partner/partner_list.html'
    context_object_name = 'partners'
    paginate_by = 50  # Domyślna liczba rekordów na stronę
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Pobierz parametry filtrowania
        search_query = self.request.GET.get('search', '')
        country_filters = self.request.GET.getlist('country')
        city_filters = self.request.GET.getlist('city')
        status_filter = self.request.GET.get('status', '')

        # Zastosuj filtrowanie wyszukiwania
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(vat_number__icontains=search_query) |
                Q(city__icontains=search_query)
            )

        # Zastosuj filtrowanie krajów
        if country_filters:
            queryset = queryset.filter(country__in=country_filters)

        # Zastosuj filtrowanie miast
        if city_filters:
            queryset = queryset.filter(city__in=city_filters)

        # Zastosuj filtrowanie statusu VAT
        if status_filter == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif status_filter == 'unverified':
            queryset = queryset.filter(is_verified=False)

        # Zastosuj paginację na podstawie wybranego rozmiaru strony
        page_size = self.request.GET.get('page_size')
        if page_size and page_size.isdigit():
            self.paginate_by = int(page_size)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Użyj funkcji add_to_context, żeby dodać spolszczone nazwy krajów
        context = add_to_context(context)

        # Pobierz już posortowane i spolszczone kraje
        sorted_countries = context['countries']

        # Przygotowanie formularza filtrowania (zachowujemy dla kompatybilności wstecznej)
        form = PartnerFilterForm(
            self.request.GET or None,
            countries=sorted_countries
        )

        # Dodanie parametrów wyszukiwania do kontekstu
        context['filter_form'] = form
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_countries'] = self.request.GET.getlist('country')
        context['selected_cities'] = self.request.GET.getlist('city')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_page_size'] = self.request.GET.get(
            'page_size', str(self.paginate_by))
        context['default_page_size'] = str(self.paginate_by)

        # Pobierz unikalne miasta dla filtra
        # Wykorzystaj set comprehension dla unikalnych wartości i posortuj
        cities = sorted({p.city for p in Partner.objects.filter(
            city__isnull=False).exclude(city='')})
        context['cities'] = cities

        return context


@login_required
def partner_create_view(request):
    """View for creating new partner"""
    # Używamy funkcji tłumaczącej nazwy krajów
    context = {}
    context = add_to_context(context)
    countries_list = context['countries']

    if request.method == 'POST':
        form = PartnerCreateForm(request.POST)

        if form.is_valid():
            partner = form.save(commit=False)

            # Verify VAT if requested
            if form.cleaned_data.get('verify_vat'):
                success, data, message, verification_id = VATVerificationService.verify_vat(
                    partner.country.code,
                    partner.vat_number
                )

                if success and data:
                    # Update partner data from verification
                    partner.is_verified = True
                    partner.verification_date = timezone.now()
                    partner.verification_id = verification_id

                    # Auto-fill fields from verification data
                    for field, value in data.items():
                        if hasattr(partner, field) and value and not getattr(partner, field):
                            setattr(partner, field, value)

                    # Save verification history
                    VATVerificationHistory.objects.create(
                        partner=partner,
                        is_verified=True,
                        verification_id=verification_id,
                        message="Weryfikacja przy tworzeniu partnera"
                    )

                    messages.success(request, _(
                        "Numer VAT zweryfikowany pomyślnie!"))
                else:
                    messages.warning(request, message or _(
                        "Nie udało się zweryfikować numeru VAT."))

            # Save partner
            partner.save()

            # Add email contacts
            email_contacts = form.cleaned_data.get('email_contacts')
            if email_contacts:
                for subscriber in email_contacts:
                    PartnerEmail.objects.create(
                        partner=partner,
                        subscriber=subscriber
                    )

            messages.success(request, _("Partner został dodany pomyślnie."))
            return redirect('partner:partner_list')
    else:
        form = PartnerCreateForm()

    context.update({
        'form': form,
        'subscribers': Subscriber.objects.all(),
        'is_new': True
    })

    return render(request, 'partner/partner_create_form.html', context)


@login_required
def partner_update_view(request, pk):
    """View for updating partner"""
    partner = get_object_or_404(Partner, pk=pk)

    # Używamy funkcji tłumaczącej nazwy krajów
    context = {}
    context = add_to_context(context)
    countries_list = context['countries']

    if request.method == 'POST':
        form = PartnerCreateForm(request.POST, instance=partner)

        if form.is_valid():
            partner = form.save()

            # Handle email contacts
            email_contacts = form.cleaned_data.get('email_contacts')

            # Remove existing relationships
            PartnerEmail.objects.filter(partner=partner).delete()

            # Add new relationships
            if email_contacts:
                for subscriber in email_contacts:
                    PartnerEmail.objects.create(
                        partner=partner,
                        subscriber=subscriber
                    )

            messages.success(request, _(
                "Partner został zaktualizowany pomyślnie."))
            return redirect('partner:partner_list')
    else:
        # Get current email contacts
        current_emails = partner.subscriber.all()

        form = PartnerCreateForm(instance=partner, initial={
            'email_contacts': current_emails,
        })

    # Get verification history
    verification_history = VATVerificationHistory.objects.filter(
        partner=partner
    ).order_by('-verification_date')[:10]

    context.update({
        'form': form,
        'partner': partner,
        'subscribers': Subscriber.objects.all(),
        'is_new': False,
        'verification_history': verification_history
    })

    return render(request, 'partner/partner_update_form.html', context)


@login_required
@require_POST
def partner_delete_view(request, pk):
    """View for deleting partner"""
    partner = get_object_or_404(Partner, pk=pk)
    partner.delete()
    messages.success(request, _("Partner został usunięty pomyślnie."))
    return redirect('partner:partner_list')


@login_required
def verify_vat_view(request, pk):
    """View for manually verifying VAT number"""
    partner = get_object_or_404(Partner, pk=pk)

    success, data, message, verification_id = VATVerificationService.verify_vat(
        partner.country.code,
        partner.vat_number
    )

    if success and data:
        # Update partner data
        partner.is_verified = True
        partner.verification_date = timezone.now()
        partner.verification_id = verification_id
        partner.save()

        # Add to verification history
        VATVerificationHistory.objects.create(
            partner=partner,
            is_verified=True,
            verification_id=verification_id,
            message="Weryfikacja wykonana ręcznie przez użytkownika"
        )

        messages.success(request, _("Numer VAT zweryfikowany pomyślnie!"))
    else:
        messages.warning(request, message or _(
            "Nie udało się zweryfikować numeru VAT."))

    return redirect('partner:partner_update', pk=pk)


@login_required
@require_GET
def fetch_mf_data(request):
    """
    Endpoint do pobierania danych z API Ministerstwa Finansów
    """
    nip = request.GET.get('nip', '')

    if not nip:
        return JsonResponse({
            'success': False,
            'message': 'Brak numeru NIP'
        })

    # Wywołanie serwisu do weryfikacji VAT
    success, data, message, verification_id = VATService.verify_vat(nip)

    return JsonResponse({
        'success': success,
        'data': data,
        'message': message
    })


# views.py
@login_required
def fetch_vies_data(request):
    """Pobieranie danych z API VIES EU"""
    country = request.GET.get('country', '')
    vat = request.GET.get('vat', '')

    if not country or not vat:
        return JsonResponse({
            'success': False,
            'message': 'Wymagane są parametry country i vat'
        })

    # Usuń znaki formatujące z numeru VAT
    vat = ''.join(c for c in vat if c.isalnum())

    # Wywołaj serwis weryfikacji VAT
    from apps.core.vat_verification import VATVerificationService
    success, data, message, verification_id = VATVerificationService._verify_eu_vat(
        country, vat)

    if success and data:
        return JsonResponse({
            'success': True,
            'data': data,
            'message': 'Numer VAT został zweryfikowany pomyślnie w systemie VIES EU.',
            'verification_id': verification_id
        })
    else:
        return JsonResponse({
            'success': False,
            'message': message or 'Nie udało się zweryfikować numeru VAT w systemie VIES EU.'
        })
