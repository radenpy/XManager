from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import logging
from .models import Partner, PartnerEmail
from apps.subscriber.models import Subscriber

# Wykorzystujemy widget z django-countries
from django_countries.widgets import CountrySelectWidget

logger = logging.getLogger(__name__)


class PartnerForm(forms.ModelForm):
    """
    Formularz do tworzenia/edycji partnera
    """
    class Meta:
        model = Partner
        fields = [
            'country', 'vat_number', 'name', 'city', 'street_name',
            'building_number', 'apartment_number', 'postal_code',
            'phone_number', 'additional_info'
        ]
        widgets = {
            'country': CountrySelectWidget(attrs={
                'class': 'form-select select2-countries',
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Wprowadź numer VAT (bez prefiksu kraju)')
            }),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'street_name': forms.TextInput(attrs={'class': 'form-control'}),
            'building_number': forms.TextInput(attrs={'class': 'form-control'}),
            'apartment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    email_contacts = forms.ModelMultipleChoiceField(
        queryset=Subscriber.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-select select2-emails'}),
        label=_('Powiązane kontakty email'),
        help_text=_('Wybierz do 10 adresów email')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Jeśli edytujemy istniejący obiekt, wstępnie wypełniamy listę powiązanych emaili
        if self.instance and self.instance.pk:
            self.fields['email_contacts'].initial = self.instance.subscriber.all()

    def clean(self):
        """Walidacja formularza"""
        cleaned_data = super().clean()

        # Sprawdzamy, czy liczba emaili nie przekracza 10
        email_contacts = cleaned_data.get('email_contacts', [])
        if len(email_contacts) > 10:
            raise ValidationError(
                _("Można dodać maksymalnie 10 powiązanych adresów email."))

        return cleaned_data

    def save(self, commit=True):
        """Zapisanie formularza z obsługą relacji M2M"""
        instance = super().save(commit=False)

        if commit:
            instance.save()

            # Zapisujemy relacje M2M (emaile)
            email_contacts = self.cleaned_data.get('email_contacts', [])

            # Usuwamy istniejące powiązania
            if instance.pk:
                PartnerEmail.objects.filter(partner=instance).delete()

            # Dodajemy nowe powiązania
            for subscriber in email_contacts:
                PartnerEmail.objects.create(
                    partner=instance, subscriber=subscriber)

        return instance


class PartnerEmailForm(forms.ModelForm):
    """
    Formularz do dodawania/edycji powiązania partnera z emailem
    """
    class Meta:
        model = PartnerEmail
        fields = ['subscriber']
        widgets = {
            'subscriber': forms.Select(attrs={'class': 'form-select select2'})
        }

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner', None)
        super().__init__(*args, **kwargs)

        if partner:
            # Wykluczamy emaile, które już są powiązane z partnerem
            excluded_subscribers = PartnerEmail.objects.filter(
                partner=partner).values_list('subscriber_id', flat=True)
            self.fields['subscriber'].queryset = Subscriber.objects.exclude(
                id__in=excluded_subscribers)

    def clean(self):
        """Walidacja formularza"""
        cleaned_data = super().clean()
        partner = self.instance.partner if self.instance and self.instance.pk else None

        if partner:
            # Sprawdzamy, czy liczba emaili nie przekracza 10
            current_count = PartnerEmail.objects.filter(
                partner=partner).count()
            if self.instance.pk is None and current_count >= 10:
                raise ValidationError(
                    _("Partner może mieć maksymalnie 10 powiązanych adresów email."))

        return cleaned_data
