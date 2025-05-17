from django.db import models
from django.contrib.auth.models import User
from apps.core.models import CoreModel
from apps.core.validators import validate_nip, validate_regon, krs_validator, validate_postal_code


class Company(CoreModel):
    name = models.CharField(max_length=255)
    tax_id = models.CharField(
        validators=[validate_nip],
        unique=True)
    tax_id_prefix = models.CharField(max_length=2, default="PL")
    regon = models.CharField(
        validators=[validate_regon],
        unique=True)
    krs = models.CharField(
        validators=[krs_validator],
        unique=True)
    street_name = models.CharField(max_length=50)
    building_number = models.CharField(max_length=10)
    appartment_number = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    post_code = models.CharField(
        validators=[validate_postal_code]
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.tax_id_prefix}{self.tax_id} {self.is_active})"

    class Meta:
        verbose_name = ('Kontrahent')
        verbose_name_plural = ('Kontrahenci')
        ordering = ['name']


class UserProfile(CoreModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company = models.ManyToManyField(Company, related_name="users")
    active_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_users"
    )
    default_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_users"
    )

    def __str__(self):
        return f"{self.user} {self.company} {self.active_company} {self.default_company}"

    class Meta:
        verbose_name = ('Profil uzytkownika')
        verbose_name_plural = ('Profil uzytkowników')
        ordering = ['user']
