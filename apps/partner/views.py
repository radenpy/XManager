# from django.shortcuts import render, redirect, get_object_or_404
# from django.urls import reverse, reverse_lazy
# from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
# from django.contrib import messages
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth.mixins import LoginRequiredMixin

# from .models import Partner, PartnerEmail
# from .forms import PartnerForm, PartnerEmailForm
# from django_countries import countries


# class PartnerListView(LoginRequiredMixin, ListView):
#     """Lista partnerów"""
#     model = Partner
#     template_name = 'partner/partner_list.html'
#     context_object_name = 'partners'
#     paginate_by = 10
#     ordering = ['name']

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         # Pobierz wszystkie kraje
#         all_countries = list(countries)

#         # Przygotuj posortowaną listę krajów
#         # 1. Polska na początku
#         # 2. Najczęściej wybierane kraje EU posortowane alfabetycznie
#         # 3. Pozostałe kraje posortowane alfabetycznie

#         # Usuń Polskę z listy krajów
#         poland = None
#         for code, name in all_countries:
#             if code == 'PL':
#                 poland = (code, name)
#                 break

#         if poland:
#             all_countries.remove(poland)

#         # Najczęściej wybierane kraje UE
#         frequently_used = [
#             'DE', 'GB', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'CZ', 'SK', 'LT', 'LV', 'EE'
#         ]

#         freq_countries = []
#         remaining_countries = []

#         # Podziel kraje na "często używane" i "pozostałe"
#         for code, name in all_countries:
#             if code in frequently_used:
#                 freq_countries.append((code, name))
#             else:
#                 remaining_countries.append((code, name))

#         # Sortuj alfabetycznie
#         freq_countries.sort(key=lambda x: x[1])  # Sortuj po nazwie kraju
#         remaining_countries.sort(key=lambda x: x[1])  # Sortuj po nazwie kraju

#         # Złóż listę z powrotem, zaczynając od Polski
#         sorted_countries = []
#         if poland:
#             sorted_countries.append(poland)
#         sorted_countries.extend(freq_countries)
#         sorted_countries.extend(remaining_countries)

#         context['countries'] = sorted_countries
#         return context


# class PartnerUpdateView(LoginRequiredMixin, UpdateView):
#     """Edycja partnera"""
#     model = Partner
#     form_class = PartnerForm
#     template_name = 'partner/partner_update.html'

#     def get_success_url(self):
#         return reverse('partner_detail', kwargs={'pk': self.object.pk})

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         # Dodaj listę krajów do kontekstu
#         context['countries'] = list(countries)

#         return context


# class PartnerDeleteView(LoginRequiredMixin, DeleteView):
#     """Usunięcie partnera"""
#     model = Partner
#     template_name = 'partner_confirm_delete.html'
#     success_url = reverse_lazy('partner_list')

#     def delete(self, request, *args, **kwargs):
#         messages.success(request, _("Partner został usunięty."))
#         return super().delete(request, *args, **kwargs)

# apps/partner/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django_countries import countries
from django.utils import timezone

from .models import Partner, PartnerEmail, VATVerificationHistory
from .forms import PartnerCreateForm, PartnerFilterForm
from apps.subscriber.models import Subscriber
from apps.core.vat_verification import VATVerificationService


class PartnerListView(LoginRequiredMixin, ListView):
    """Lista partnerów"""
    model = Partner
    template_name = 'partner/partner_list.html'
    context_object_name = 'partners'
    paginate_by = 10
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Apply filters from form
        search_query = self.request.GET.get('search', '')
        country = self.request.GET.get('country', '')
        status = self.request.GET.get('status', '')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        if country:
            queryset = queryset.filter(country=country)

        if status == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif status == 'unverified':
            queryset = queryset.filter(is_verified=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prepare countries for filter form
        all_countries = list(countries)

        # Prepare filter form
        form = PartnerFilterForm(
            self.request.GET or None,
            countries=all_countries
        )

        context['filter_form'] = form
        context['countries'] = all_countries
        return context


@login_required
def partner_create_view(request):
    """View for creating new partner"""
    all_countries = list(countries)

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

    return render(request, 'partner/partner_form.html', {
        'form': form,
        'countries': all_countries,
        'subscribers': Subscriber.objects.all(),
        'is_new': True
    })


@login_required
def partner_update_view(request, pk):
    """View for updating partner"""
    partner = get_object_or_404(Partner, pk=pk)
    all_countries = list(countries)

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

    return render(request, 'partner/partner_form.html', {
        'form': form,
        'partner': partner,
        'countries': all_countries,
        'subscribers': Subscriber.objects.all(),
        'is_new': False,
        'verification_history': verification_history
    })


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
