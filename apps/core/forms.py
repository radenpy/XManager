from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import logging
from apps.partners.models import Partner, PartnerEmail
from apps.subscribers.models import Subscriber
from apps.core.vat_verification import VATVerificationService

# Wykorzystujemy widget z django-countries
from django_countries.widgets import CountrySelectWidget

logger = logging.getLogger(__name__)


class VATVerificationForm(forms.Form):
    """
    Formularz do weryfikacji numeru VAT (używany w widoku AJAX)
    """
    country = forms.CharField(
        max_length=2,
        widget=forms.HiddenInput()
    )
    vat_number = forms.CharField(
        max_length=20,
        widget=forms.HiddenInput()
    )

    def clean(self):
        """Walidacja formularza"""
        cleaned_data = super().clean()
        country = cleaned_data.get('country')
        vat_number = cleaned_data.get('vat_number')

        if not country or not vat_number:
            return cleaned_data

        # Usuwamy spacje i myślniki z numeru VAT
        vat_number = ''.join(c for c in vat_number if c.isalnum())
        cleaned_data['vat_number'] = vat_number

        return cleaned_data

    def verify_vat(self):
        """
        Weryfikacja numeru VAT w odpowiednim API
        """
        country = self.cleaned_data.get('country')
        vat_number = self.cleaned_data.get('vat_number')

        # Weryfikacja VAT przy użyciu serwisu
        success, data, message, verification_id = VATVerificationService.verify_vat(
            country, vat_number)

        # Przygotujemy dane do zwrócenia
        if success:
            if data:
                data['verification_id'] = verification_id

        return {
            'success': success,
            'data': data,
            'message': message
        }
