from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from apps.core.models import CoreModel
from apps.core.validators import validate_nip, validate_regon, krs_validator, validate_postal_code


class Company(CoreModel):
    name = models.CharField(max_length=255, verbose_name="Nazwa")
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Kod firmy",
        help_text="Kod używany w numeracji dokumentów (np. ABC, XYZ)",
        validators=[RegexValidator(
            r'^[A-Za-z0-9]+$', 'Kod może zawierać tylko litery i cyfry')]
    )
    tax_id = models.CharField(
        max_length=10,
        validators=[validate_nip],
        unique=True,
        verbose_name="NIP"
    )
    tax_id_prefix = models.CharField(
        max_length=2,
        default="PL",
        verbose_name="Prefiks NIP"
    )
    regon = models.CharField(
        max_length=14,
        validators=[validate_regon],
        unique=True,
        blank=True,
        null=True,
        verbose_name="REGON"
    )
    krs = models.CharField(
        max_length=10,
        validators=[krs_validator],
        unique=True,
        blank=True,
        null=True,
        verbose_name="KRS"
    )
    street_name = models.CharField(
        max_length=50,
        verbose_name="Ulica"
    )
    building_number = models.CharField(
        max_length=10,
        verbose_name="Numer budynku"
    )
    appartment_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="Numer lokalu"
    )
    city = models.CharField(
        max_length=50,
        verbose_name="Miasto"
    )
    post_code = models.CharField(
        max_length=6,
        validators=[validate_postal_code],
        verbose_name="Kod pocztowy"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktywny"
    )

    def save(self, *args, **kwargs):
        # Automatyczna konwersja kodu na wielkie litery
        if self.code:
            self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.tax_id_prefix}{self.tax_id} {self.is_active})"

    class Meta:
        verbose_name = ('Firma')
        verbose_name_plural = ('Firmy')
        ordering = ['name']


class UserProfile(CoreModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Użytkownik"
    )
    company = models.ManyToManyField(
        Company,
        related_name="users",
        verbose_name="Firmy"
    )
    active_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_users",
        verbose_name="Aktywna firma"
    )
    default_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_users",
        verbose_name="Domyślna firma"
    )

    def __str__(self):
        return f"{self.user} {self.company} {self.active_company} {self.default_company}"

    class Meta:
        verbose_name = ('Profil uzytkownika')
        verbose_name_plural = ('Profil uzytkowników')
        ordering = ['user']
