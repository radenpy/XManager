from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

# Dodajemy obie wersje URL-i dla bezpieczeństwa
EXEMPT_URLS = [
    '/admin/',
    '/login/',
    '/logout/',
    '/choose-company/',  # Wersja z myślnikiem
    '/choose_company/',  # Wersja bez myślnika
]


class ActiveCompanyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        # Sprawdzamy czy URL jest na liście wyjątków
        if any(request.path.startswith(url) for url in EXEMPT_URLS):
            return None

        # Sprawdzenie czy istnieje profil - jeśli nie, nie przekierowujemy, bo to może powodować pętlę
        try:
            profile = request.user.userprofile
        except:
            # Jeśli nie ma profilu, nie przekierowujemy, bo może to powodować pętlę
            return None

        # Sprawdzamy czy użytkownik ma firmę
        if hasattr(profile, 'active_company') and profile.active_company is None:
            # Sprawdzamy czy użytkownik ma jakiekolwiek firmy
            if hasattr(profile, 'company') and profile.company.exists():
                # Jeśli ma firmy, ale nie ma aktywnej, przekieruj do wyboru firmy
                return redirect('choose_company')
            else:
                # Jeśli nie ma firm, nie przekierowuj do wyboru firmy (to by spowodowało pętlę)
                return None

        # Dodajemy aktywną firmę do requestu, jeśli istnieje
        if hasattr(profile, 'active_company') and profile.active_company:
            request.company = profile.active_company

        return None
