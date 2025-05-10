
# apps/partner/forms.py
from django import forms
from django_countries.fields import CountryField
from .models import Partner, PartnerEmail
from apps.subscriber.models import Subscriber


class PartnerFilterForm(forms.Form):
    """Form for filtering partners"""
    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Wyszukaj...'}))
    country = forms.ChoiceField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=(
            ('', 'Status VAT'),
            ('verified', 'Aktywny'),
            ('unverified', 'Nieaktywny'),
        ),
    )

    def __init__(self, *args, **kwargs):
        countries_list = kwargs.pop('countries', [])
        super().__init__(*args, **kwargs)
        self.fields['country'].choices = [
            ('', 'Wszystkie kraje')] + list(countries_list)


class PartnerCreateForm(forms.ModelForm):
    """Form for creating new partner"""
    email_contacts = forms.ModelMultipleChoiceField(
        queryset=Subscriber.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        help_text='Wybierz powiązane adresy email (maksymalnie 10)'
    )

    verify_vat = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Partner
        fields = [
            'country', 'vat_number', 'name', 'city',
            'street_name', 'building_number', 'apartment_number',
            'postal_code', 'phone_number', 'additional_info'
        ]
        widgets = {
            'country': forms.Select(attrs={'class': 'form-select'}),
            'vat_number': forms.TextInput(attrs={'placeholder': 'Wprowadź numer VAT (bez prefiksu kraju)'}),
        }
