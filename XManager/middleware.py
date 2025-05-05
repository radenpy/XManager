from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

EXEMPT_URLS = [
    '/admin/',
    '/login/',
    '/logout/',
    '/choose-company/',
]


class ActiveCompanyMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        if any(request.path.startswith(url) for url in EXEMPT_URLS):
            return None

        profile = getattr(request.user, 'userprofile', None)
        if profile:
            if not profile.active_company:
                # Zawsze kieruj na wybór kontekstu jeśli nie ustawiony
                return redirect("choose_company")
            request.company = profile.active_company
