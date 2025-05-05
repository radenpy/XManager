# managers.py

from django.db import models
from apps.core.utils import get_current_request


class CompanyModelManager(models.Manager):
    def get_queryset(self):
        # Pobierz bieżące żądanie z thread local storage
        request = get_current_request()  # Funkcja do zaimplementowania

        if hasattr(request, 'company') and request.company:
            return super().get_queryset().filter(company=request.company)
        elif hasattr(request, 'session') and request.session.get('is_master_view'):
            # Widok administratora - wszystkie dane
            return super().get_queryset()
        else:
            # Domyślnie - puste QuerySet dla bezpieczeństwa
            return super().get_queryset().none()
