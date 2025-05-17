# apps/docnum/api.py

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .services import DocumentNumberService


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_document_number(request):
    """API do generowania numerów dokumentów"""
    data = request.data
    company_code = data.get('company_code')
    document_type = data.get('document_type')
    warehouse_number = data.get('warehouse_number', None)

    if not company_code or not document_type:
        return JsonResponse({'error': 'Brak wymaganych parametrów'}, status=400)

    document_number = DocumentNumberService.generate_number(
        company_code=company_code,
        document_type=document_type,
        warehouse_number=warehouse_number
    )

    return JsonResponse({'document_number': document_number})
