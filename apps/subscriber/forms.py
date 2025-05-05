from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Subscriber, SubscriberGroup


class SubscriberForm(forms.ModelForm):
    """Formularz dla modelu Subscriber"""

    class Meta:
        model = Subscriber
        fields = ['email', 'first_name', 'last_name',
                  'newsletter_consent', 'group_affiliation']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'newsletter_consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'group_affiliation': forms.SelectMultiple(attrs={'class': 'form-control select2-multiple'})
        }

    def clean_email(self):
        """Walidacja adresu email"""
        email = self.cleaned_data.get('email')

        # Sprawdź, czy email jest unikalny
        if Subscriber.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise ValidationError(
                _("Subskrybent z tym adresem email już istnieje."))

        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dodaj dodatkowe klasy CSS i placeholder
        self.fields['email'].widget.attrs.update({
            'placeholder': _('Wprowadź adres email')
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': _('Wprowadź imię')
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': _('Wprowadź nazwisko')
        })

        # Dodaj opis dla pola newsletter_consent
        self.fields['newsletter_consent'].help_text = _(
            'Zaznacz, jeśli subskrybent wyraził zgodę na otrzymywanie newslettera.')

        # Posortuj grupy alfabetycznie
        self.fields['group_affiliation'].queryset = SubscriberGroup.objects.all(
        ).order_by('group_name')


class SubscriberGroupForm(forms.ModelForm):
    """Formularz dla modelu SubscriberGroup"""

    class Meta:
        model = SubscriberGroup
        fields = ['group_name']
        widgets = {
            'group_name': forms.TextInput(attrs={'class': 'form-control'})
        }

    def clean_group_name(self):
        """Walidacja nazwy grupy"""
        group_name = self.cleaned_data.get('group_name')

        # Sprawdź, czy nazwa grupy jest unikalna
        if SubscriberGroup.objects.filter(group_name=group_name).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
            raise ValidationError(_("Grupa o tej nazwie już istnieje."))

        return group_name
