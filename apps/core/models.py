from django.db import models
from django.conf import settings


class CoreModel(models.Model):
    """
    Abstrakcyjny model bazowy zawierający pola wspólne dla większości modeli w systemie.
    Śledzi czas utworzenia/aktualizacji oraz użytkowników odpowiedzialnych za te operacje.
    """
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Data aktualizacji")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name="Utworzony przez"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(app_label)s_%(class)s_updated",
        verbose_name="Zaktualizowany przez"
    )

    class Meta:
        abstract = True
