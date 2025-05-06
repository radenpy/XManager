from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import CoreModel
from apps.core.validators import phone_number_validator
from apps.core.vat_verification import VATVerificationService, EU_COUNTRY_CODES

from django_countries.fields import CountryField
import logging

# Create your models here.

logger = logging.getLogger(__name__)


class PartnerEmail(CoreModel):
    """Model przechowujący powiązania między partnerem a subskrybentami (email)"""

    partner = models.ForeignKey(
        'Partner', on_delete=models.CASCADE, related_name='emails')
    subscriber = models.ForeignKey(
        'subscriber.Subscriber', on_delete=models.CASCADE, related_name='partners')

    class Meta:
        verbose_name = ('Partner Email')
        verbose_name_plural = ('Partner Emails')
        unique_together = ('partner', 'subscriber')

    def __str__(self):
        return f"{self.partner.name} - {self.subscriber.email}"


class Partner(CoreModel):
    """
    Model Partnera z weryfikacją VAT i autouzupełnianiem danych
    """
    # Używamy CountryField z django-countries zamiast zwykłego CharField
    country = CountryField(
        verbose_name=('Kraj'),
        help_text=(
            'Choose country, to specify a method of VAT number verification')
    )

    vat_number = models.CharField(
        max_length=20,
        verbose_name=('VAT number'),
        help_text=('Enter VAT number without country prefix')
    )
    # jeśli kraj Polska to walidacja z bazy ministerstwa finansow,
    # jesli kraj w obrębie EU to walidacja z api komisji europejskiej

    # Pola uzupełniane automatycznie po weryfikacji VAT
    name = models.CharField(
        max_length=100,
        verbose_name='Company name',
        blank=True,
        editable=True
    )

    name_verified = models.BooleanField(
        default=False,
        verbose_name=('Verified Name'),
        editable=True
    )

    # Adres uzupełniany automatycznie po weryfikacji VAT
    city = models.CharField(
        max_length=100,
        verbose_name=('City'),
        blank=True,
        editable=True
    )

    street_name = models.CharField(
        max_length=100,
        verbose_name=('Street'),
        blank=True,
        editable=True
    )

    building_number = models.CharField(
        max_length=100,
        verbose_name=('Building number'),
        blank=True,
        editable=True
    )

    apartment_number = models.CharField(
        max_length=10,
        verbose_name=('Apartment number'),
        blank=True,
        null=True,
        editable=True
    )

    postal_code = models.CharField(
        max_length=10,
        verbose_name=('Postal code'),
        blank=True,
        editable=True

    )

    # Dodatkowe dane
    phone_number = models.CharField(
        validators=[phone_number_validator],
        verbose_name=('Phone number'),
        blank=True
    )

    additional_info = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=('Additional information')
    )

    # Status weryfikacji
    is_verified = models.BooleanField(
        default=False,
        verbose_name=('Verified'),
        editable=False
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=('Verification date'),
        editable=False
    )

    verification_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=('Verification ID'),
        help_text=('Unique query ID from government verification API system'),
        editable=False
    )

    # Powiązanie z modelem subscriber (many to many)

    subscriber = models.ManyToManyField(
        'subscriber.Subscriber',
        through='PartnerEmail',
        related_name='partnered_with',
        verbose_name=('Email contacts'),
        help_text=('Max 10 email addresses')
    )

    def __str__(self):
        return f"{self.name} ({self.get_full_vat_number()})"

    def get_full_vat_number(self):
        """Zwraca pełny numer VAT z prefiksem kraju"""
        return f"{self.country.code}{self.vat_number}"

    def verify_vat(self):
        """
        Weryfikuje numer VAT i aktualizuje dane modelu
        """
        success, data, message, verification_id = VATVerificationService.verify_vat(
            self.country.code,
            self.vat_number
        )

        if success and data:
            # Uzupełniamy dane na podstawie weryfikacji
            for field, value in data.items():
                if hasattr(self, field) and value:
                    setattr(self, field, value)

            self.is_verified = True
            self.verfication_date = timezone.now()
            self.verfication_id = verification_id
            self.save()

        return success, message

    def clean(self):
        """Walidacja modelu"""
        super().clean()

        # # Formatowanie tekstu - pierwsza litera wielka, reszta małe
        # if self.name:
        #     self.name = self.name.title()
        # if self.city:
        #     self.city = self.city.title()
        # if self.street_name:
        #     self.street_name = self.street_name.title()

        # Sprawdzanie czy liczba powiązanych emaili nie przekracza 10

        if hasattr(self, 'id') and self.id and self.emails.count() > 10:
            raise ValidationError(
                {'subscriber': ('Partner moze mieć maksymalnie 10 powiązanych adresów email')})

    class Meta:
        verbose_name = ('Partner')
        verbose_name_plural = ('Partners')
        # Unikalny numer VAT dla danego kraju
        unique_together = [('country', 'vat_number')]


class VATVerificationHistory(CoreModel):
    """Model to store VAT verification history"""
    partner = models.ForeignKey(
        'Partner', on_delete=models.CASCADE, related_name='vat_verification_history')
    verification_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Data weryfikacji')
    is_verified = models.BooleanField(
        default=False, verbose_name='Zweryfikowany')
    verification_id = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='ID weryfikacji')
    message = models.TextField(blank=True, null=True, verbose_name='Wiadomość')

    class Meta:
        verbose_name = 'Historia weryfikacji VAT'
        verbose_name_plural = 'Historie weryfikacji VAT'
        ordering = ['-verification_date']
