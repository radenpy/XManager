from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
import json

from .models import Partner, PartnerEmail
from .forms import PartnerForm, PartnerEmailForm
from apps.subscriber.models import Subscriber
from apps.core.vat_verification import VATVerificationService, EU_COUNTRY_CODES

from django_countries import countries


class PartnerListView(LoginRequiredMixin, ListView):
    """Lista partnerów"""
    model = Partner
    template_name = 'partner/partner_list.html'
    context_object_name = 'partners'
    paginate_by = 10
    ordering = ['name']  # Dodaje domyślne sortowanie po ID (malejąco)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pobierz wszystkie kraje
        all_countries = list(countries)

        # Przygotuj posortowaną listę krajów
        # 1. Polska na początku
        # 2. Najczęściej wybierane kraje EU posortowane alfabetycznie
        # 3. Pozostałe kraje posortowane alfabetycznie

        # Usuń Polskę z listy krajów
        poland = None
        for code, name in all_countries:
            if code == 'PL':
                poland = (code, name)
                break

        if poland:
            all_countries.remove(poland)

        # Najczęściej wybierane kraje UE
        frequently_used = [
            'DE', 'GB', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'CZ', 'SK', 'LT', 'LV', 'EE'
        ]

        freq_countries = []
        remaining_countries = []

        # Podziel kraje na "często używane" i "pozostałe"
        for code, name in all_countries:
            if code in frequently_used:
                freq_countries.append((code, name))
            else:
                remaining_countries.append((code, name))

        # Sortuj alfabetycznie
        freq_countries.sort(key=lambda x: x[1])  # Sortuj po nazwie kraju
        remaining_countries.sort(key=lambda x: x[1])  # Sortuj po nazwie kraju

        # Złóż listę z powrotem, zaczynając od Polski
        sorted_countries = []
        if poland:
            sorted_countries.append(poland)
        sorted_countries.extend(freq_countries)
        sorted_countries.extend(remaining_countries)

        context['countries'] = sorted_countries
        return context


class PartnerCreateAPIView(LoginRequiredMixin, View):
    """
    API do tworzenia nowego partnera (AJAX)
    """

    def post(self, request, *args, **kwargs):
        # Pobierz dane z requesta
        country = request.POST.get('country')
        vat_number = request.POST.get('vat_number')
        name = request.POST.get('name')
        city = request.POST.get('city')
        street_name = request.POST.get('street_name')
        building_number = request.POST.get('building_number')
        apartment_number = request.POST.get('apartment_number')
        postal_code = request.POST.get('postal_code')
        phone_number = request.POST.get('phone_number')
        additional_info = request.POST.get('additional_info')
        verification_id = request.POST.get('verification_id')
        email_contacts = request.POST.getlist('email_contacts')

        try:
            # Stwórz nowego partnera
            partner = Partner(
                country=country,
                vat_number=vat_number,
                name=name,
                city=city,
                street_name=street_name,
                building_number=building_number,
                apartment_number=apartment_number,
                postal_code=postal_code,
                phone_number=phone_number,
                additional_info=additional_info,
                verification_id=verification_id,
                is_verified=True
            )

            # Ustaw pola weryfikacji
            if verification_id:
                partner.verification_id = verification_id  # Poprawiona nazwa pola
                partner.verification_date = timezone.now()  # Poprawiona nazwa pola

            partner.save()

            # Dodaj powiązane emaile
            if email_contacts:
                for email_id in email_contacts:
                    try:
                        # Sprawdź, czy to istniejący subskrybent czy nowy email
                        if email_id.isdigit():
                            # Istniejący subskrybent
                            subscriber = Subscriber.objects.get(pk=email_id)
                        else:
                            # Nowy email - sprawdź, czy już istnieje
                            try:
                                subscriber = Subscriber.objects.get(
                                    email=email_id)
                            except Subscriber.DoesNotExist:
                                # Stwórz nowego subskrybenta
                                subscriber = Subscriber(
                                    email=email_id,
                                    first_name='',
                                    last_name='',
                                    newsletter_consent=True
                                )
                                subscriber.save()

                        # Dodaj powiązanie
                        PartnerEmail.objects.create(
                            partner=partner,
                            subscriber=subscriber
                        )
                    except Exception as e:
                        # Log błędu przy dodawaniu emaila
                        print(f"Błąd dodawania emaila {email_id}: {str(e)}")

            # Zwróć sukces
            return JsonResponse({
                'success': True,
                'message': _("Partner został dodany pomyślnie."),
                'partner_id': partner.id
            })
        except Exception as e:
            # Zwróć błąd
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


# Pobieranie danych partnera
# Pobieranie danych partnera
class PartnerGetAPIView(LoginRequiredMixin, View):
    """
    API do pobierania danych partnera (AJAX)
    """

    def get(self, request, partner_id, *args, **kwargs):
        try:
            partner = Partner.objects.get(pk=partner_id)

            # Przygotuj dane do zwrócenia
            data = {
                'id': partner.id,
                'name': partner.name,
                # Zmiana z partner.country na partner.country.code
                'country_code': partner.country.code,
                # Prosta konwersja na string
                'country_name': str(partner.country.name),
                'vat_number': partner.vat_number,
                'city': partner.city,
                'street_name': partner.street_name,
                'building_number': partner.building_number,
                'apartment_number': partner.apartment_number,
                'postal_code': partner.postal_code,
                'phone_number': partner.phone_number,
                'additional_info': partner.additional_info,
                'emails': []
            }

            # Dodaj powiązane emaile
            partner_emails = PartnerEmail.objects.filter(partner=partner)
            for partner_email in partner_emails:
                data['emails'].append({
                    'id': partner_email.subscriber.id,
                    'email': partner_email.subscriber.email
                })

            return JsonResponse({
                'success': True,
                'data': data
            })
        except Partner.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Partner nie istnieje"
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Dodajemy pełny ślad błędu
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

# Aktualizacja partnera


class PartnerUpdateAPIView(LoginRequiredMixin, View):
    """
    API do aktualizacji partnera (AJAX)
    """

    def post(self, request, partner_id, *args, **kwargs):
        try:
            partner = Partner.objects.get(pk=partner_id)

            # Aktualizuj dane partnera
            if 'name' in request.POST:
                partner.name = request.POST.get('name')
            if 'city' in request.POST:
                partner.city = request.POST.get('city')
            if 'street_name' in request.POST:
                partner.street_name = request.POST.get('street_name')
            if 'building_number' in request.POST:
                partner.building_number = request.POST.get('building_number')
            if 'apartment_number' in request.POST:
                partner.apartment_number = request.POST.get('apartment_number')
            if 'postal_code' in request.POST:
                partner.postal_code = request.POST.get('postal_code')
            if 'phone_number' in request.POST:
                partner.phone_number = request.POST.get('phone_number')
            if 'additional_info' in request.POST:
                partner.additional_info = request.POST.get('additional_info')

            # Zapisz zmiany
            partner.save()

            # Aktualizuj powiązane adresy email
            if 'email_contacts' in request.POST:
                # Usuń istniejące powiązania
                partner.emails.clear()

                # Dodaj nowe powiązania
                email_ids = request.POST.getlist('email_contacts')
                for email_id in email_ids:
                    # Jeśli to nowy email (string, a nie ID)
                    if not email_id.isdigit():
                        # Utwórz nowy adres email
                        subscriber, created = Subscriber.objects.get_or_create(
                            email=email_id,
                            defaults={'email': email_id}
                        )
                        partner.emails.add(subscriber)
                    else:
                        # Dodaj istniejący adres email
                        try:
                            subscriber = Subscriber.objects.get(
                                pk=int(email_id))
                            partner.emails.add(subscriber)
                        except Subscriber.DoesNotExist:
                            pass

            return JsonResponse({
                'success': True,
                'message': "Partner został zaktualizowany pomyślnie"
            })
        except Partner.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Partner nie istnieje"
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


class PartnerUpdateView(LoginRequiredMixin, UpdateView):
    """Edycja partnera"""
    model = Partner
    form_class = PartnerForm
    template_name = 'partner/partner_update.html'

    def get_success_url(self):
        return reverse('partners:partner_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Dodaj listę krajów do kontekstu
        context['countries'] = list(countries)

        return context


class PartnerDeleteView(LoginRequiredMixin, DeleteView):
    """Usunięcie partnera"""
    model = Partner
    template_name = 'partners/partner_confirm_delete.html'
    success_url = reverse_lazy('partner:partner_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Partner został usunięty."))
        return super().delete(request, *args, **kwargs)


class VerifyVATAPIView(LoginRequiredMixin, View):
    """
    API do weryfikacji numeru VAT (AJAX)
    """

    def get(self, request, *args, **kwargs):
        country = request.GET.get('country', '')
        vat_number = request.GET.get('vat_number', '')

        if not country or not vat_number:
            return JsonResponse({
                'success': False,
                'data': None,
                'message': _("Nieprawidłowe dane wejściowe.")
            })

        # Weryfikacja VAT przy użyciu serwisu
        success, data, message, verification_id = VATVerificationService.verify_vat(
            country, vat_number)

        # Dodaj informację o konieczności ręcznego wypełnienia, jeśli dane są puste
        if success and (not data.get('name') or data.get('name') == '---'):
            data['manual_input_required'] = True
            message += " Dane firmy nie są dostępne, wypełnij je ręcznie."

        return JsonResponse({
            'success': success,
            'data': data,
            'message': message
        })


class SubscriberLookupAPIView(LoginRequiredMixin, View):
    """
    API do wyszukiwania subskrybentów po adresie email (AJAX)
    """

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        limit = 10

        # Wyszukaj subskrybentów
        if search:
            subscribers = Subscriber.objects.filter(email__icontains=search)
        else:
            subscribers = Subscriber.objects.all()

        # Paginacja
        start = (page - 1) * limit
        end = page * limit

        # Przygotuj dane
        total = subscribers.count()
        results = []

        for subscriber in subscribers[start:end]:
            results.append({
                'id': subscriber.id,
                'email': subscriber.email,
                'first_name': subscriber.first_name,
                'last_name': subscriber.last_name
            })

        return JsonResponse({
            'results': results,
            'has_more': total > end
        })
