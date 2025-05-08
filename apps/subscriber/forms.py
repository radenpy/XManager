from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from .models import Subscriber, SubscriberGroup


class SubscriberForm(forms.ModelForm):
    """Formularz dla modelu Subscriber"""

    class Meta:
        model = Subscriber
        fields = ['email', 'common_name', 'first_name', 'last_name',
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

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Wprowadź poprawny adres e-mail")

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

# Add this to apps/subscriber/forms.py


class SubscriberImportForm(forms.Form):
    """Form for importing subscribers via text input"""
    import_type = forms.ChoiceField(
        choices=[('text', 'Wklej adresy email'), ('file', 'Importuj z pliku')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input me-2'}),
        initial='text',
        label='Metoda importu'
    )

    email_list = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Wklej adresy email (jeden w linii lub oddzielone przecinkami)'
        }),
        required=False,
        label='Lista adresów email'
    )

    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False,
        label='Plik Excel (.xlsx, .xls, .ods)',
        help_text='Kolumny pliku powinny mieć nazwy: email, nazwa, imię, nazwisko, zgoda'
    )

    newsletter_consent = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Zgoda na newsletter'
    )

    group_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'form-check-input'}),
        label='Przypisz do grup'
    )

    partner_ids = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={'class': 'form-check-input'}),
        label='Przypisz do firm'
    )

    # Create a new group during import
    new_group = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwa nowej grupy'
        }),
        label='Utwórz nową grupę'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add groups as choices
        groups = SubscriberGroup.objects.all().order_by('group_name')
        self.fields['group_ids'].choices = [
            (group.id, group.group_name) for group in groups]

        # Add partners as choices
        from apps.partner.models import Partner
        partners = Partner.objects.all().order_by('name')
        self.fields['partner_ids'].choices = [
            (partner.id, partner.name) for partner in partners]

    def clean(self):
        cleaned_data = super().clean()
        import_type = cleaned_data.get('import_type')
        email_list = cleaned_data.get('email_list')
        import_file = cleaned_data.get('file')

        if import_type == 'text' and not email_list:
            self.add_error(
                'email_list', 'Podaj listę adresów email do importu')

        if import_type == 'file' and not import_file:
            self.add_error('file', 'Wybierz plik do importu')

        if import_file and import_type == 'file':
            ext = import_file.name.split('.')[-1].lower()
            if ext not in ['xlsx', 'xls', 'ods']:
                self.add_error(
                    'file', 'Dozwolone formaty plików: .xlsx, .xls, .ods')

        # Check if creating a new group
        new_group = cleaned_data.get('new_group')
        if new_group:
            # Check if group name is unique
            if SubscriberGroup.objects.filter(group_name=new_group).exists():
                self.add_error('new_group', 'Grupa o tej nazwie już istnieje')

        return cleaned_data
