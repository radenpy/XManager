# middleware.py
from django.shortcuts import get_object_or_404
from apps.core.utils import set_current_request
from apps.company.models import Company


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        return response


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Sprawdź, czy użytkownik jest zalogowany
        if request.user.is_authenticated:
            # Pobierz firmę z sesji lub ustaw domyślną
            company_id = request.session.get('company_id')
            if company_id:
                # pylint: disable=no-member
                request.company = Company.objects.get(id=company_id)
            else:
                # Domyślna firma lub None
                request.company = None
        else:
            request.company = None

        response = self.get_response(request)
        return response
