from django.views import View
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Partner, PartnerEmail, VATVerificationHistory
from apps.subscriber.models import Subscriber
from apps.core.vat_verification import VATVerificationService, EU_COUNTRY_CODES


class PartnerGetAPIView(LoginRequiredMixin, View):
    """
    API do pobierania danych partnera (AJAX)
    """

    def get(self, request, partner_id, *args, **kwargs):
        try:
            partner = Partner.objects.get(pk=partner_id)

            # Pobierz historię weryfikacji
            verification_history = VATVerificationHistory.objects.filter(
                partner=partner).order_by('-verification_date')[:10]

            history_data = []
            for entry in verification_history:
                history_data.append({
                    'verification_date': entry.verification_date.isoformat(),
                    'is_verified': entry.is_verified,
                    'verification_id': entry.verification_id or '',
                    'message': entry.message or ''
                })

            # Przygotuj dane do zwrócenia
            data = {
                'id': partner.id,
                'name': partner.name,
                'country_code': partner.country.code,
                'country_name': str(partner.country.name),
                'vat_number': partner.vat_number,
                'city': partner.city,
                'street_name': partner.street_name,
                'building_number': partner.building_number,
                'apartment_number': partner.apartment_number,
                'postal_code': partner.postal_code,
                'phone_number': partner.phone_number,
                'additional_info': partner.additional_info,
                'is_verified': partner.is_verified,
                'verification_date': partner.verification_date.isoformat() if partner.verification_date else None,
                'verification_id': partner.verification_id or '',
                'verification_history': history_data,
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
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


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
                partner.verification_id = verification_id
                partner.verification_date = timezone.now()

                # Dodaj wpis do historii weryfikacji
                VATVerificationHistory.objects.create(
                    partner=partner,
                    is_verified=True,
                    verification_id=verification_id,
                    message="Weryfikacja przy tworzeniu partnera"
                )

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


class PartnerUpdateAPIView(LoginRequiredMixin, View):
    """
    API do aktualizacji partnera (AJAX)
    """

    def post(self, request, partner_id, *args, **kwargs):
        try:
            partner = get_object_or_404(Partner, pk=partner_id)

            # Debug: Log what we're receiving
            print(f"Received data for partner {partner_id}:")
            print(
                f"Email contacts in POST: {request.POST.getlist('email_contacts')}")

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

            # ALWAYS delete all existing email relationships, even if not sending new ones
            email_count_before = PartnerEmail.objects.filter(
                partner=partner).count()
            print(
                f"Before deletion, partner had {email_count_before} email relationships")

            PartnerEmail.objects.filter(partner=partner).delete()
            print(f"All email relationships deleted")

            # Add new email relationships if any are provided
            if 'email_contacts' in request.POST:
                email_ids = request.POST.getlist('email_contacts')
                print(
                    f"Adding {len(email_ids)} new email relationships: {email_ids}")

                for email_id in email_ids:
                    # Jeśli to nowy email (string, a nie ID)
                    if not email_id.isdigit():
                        # Utwórz nowy adres email
                        subscriber, created = Subscriber.objects.get_or_create(
                            email=email_id,
                            defaults={'first_name': '', 'last_name': '',
                                      'newsletter_consent': True}
                        )
                        print(
                            f"Created new subscriber: {subscriber.email}, ID: {subscriber.id}")
                    else:
                        # Pobierz istniejący adres email
                        try:
                            subscriber = Subscriber.objects.get(
                                pk=int(email_id))
                            print(
                                f"Found existing subscriber: {subscriber.email}, ID: {subscriber.id}")
                        except Subscriber.DoesNotExist:
                            print(
                                f"Subscriber with ID {email_id} not found, skipping")
                            continue

                    # Zawsze twórz nowe powiązanie
                    partner_email, created = PartnerEmail.objects.get_or_create(
                        partner=partner, subscriber=subscriber)
                    print(
                        f"Created relationship: {partner.id} - {subscriber.id}")

            # Final count check
            email_count_after = PartnerEmail.objects.filter(
                partner=partner).count()
            print(
                f"After update, partner has {email_count_after} email relationships")

            return JsonResponse({
                'success': True,
                'message': "Partner został zaktualizowany pomyślnie"
            })
        except Exception as e:
            import traceback
            print(f"Error updating partner: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': str(e)
            })


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

        # Zamiast zwracać tylko informację o niepowodzeniu, dodaj opcję kontynuacji
        if not success:
            # Dodaj dane domyślne do ręcznego wypełnienia
            data = {
                'manual_input_required': True,
                'name': '',
                'city': '',
                'street_name': '',
                'building_number': '',
                'postal_code': '',
                'is_vat_registered': False  # Nowe pole informujące o statusie VAT
            }

        return JsonResponse({
            'success': True,  # Zawsze zwracaj sukces, żeby formularz mógł kontynuować
            'vat_verified': success,  # Nowe pole informujące czy VAT został zweryfikowany
            'data': data,
            'message': message
        })


class SubscriberLookupAPIView(LoginRequiredMixin, View):
    """
    API do wyszukiwania subskrybentów po adresie email, imieniu lub nazwisku (AJAX)
    """

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        limit = 10

        # Wyszukaj subskrybentów
        if search:
            subscribers = Subscriber.objects.filter(
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
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


class UpdateVerificationAPIView(LoginRequiredMixin, View):
    """API to update partner verification status"""

    def post(self, request, pk):
        partner = get_object_or_404(Partner, pk=pk)

        # Pobranie danych
        is_verified = request.POST.get('is_verified') == 'true'
        verification_id = request.POST.get('verification_id', '')

        # Update verification status
        partner.is_verified = is_verified
        partner.verification_date = timezone.now()
        partner.verification_id = verification_id
        partner.save()

        # Add to verification history
        VATVerificationHistory.objects.create(
            partner=partner,
            is_verified=is_verified,
            verification_id=verification_id,
            message="Weryfikacja wykonana przez użytkownika"
        )

        # Get all verification history for this partner
        history = VATVerificationHistory.objects.filter(
            partner=partner).order_by('-verification_date')[:10]

        # Prepare history data for response
        history_data = []
        for entry in history:
            history_data.append({
                'verification_date': entry.verification_date.isoformat(),
                'is_verified': entry.is_verified,
                'verification_id': entry.verification_id or '',
                'message': entry.message or ''
            })

        return JsonResponse({
            'success': True,
            'message': 'Status weryfikacji został zaktualizowany.',
            'history': history_data
        })
