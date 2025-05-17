# apps/docnum/services.py

from django.db import transaction
from datetime import datetime
from .models import DocumentSequence


class DocumentNumberService:
    """Serwis do generowania numerów dokumentów"""

    @staticmethod
    @transaction.atomic
    def generate_number(company_code, document_type, warehouse_number=None, date=None):
        """
        Generuje unikalny numer dokumentu

        Args:
            company_code (str): Kod firmy
            document_type (str): Typ dokumentu (np. WZ, PZ, FV)
            warehouse_number (str, optional): Numer magazynu (dla dokumentów magazynowych)
            date (datetime, optional): Data dokumentu (domyślnie obecna data)

        Returns:
            str: Wygenerowany numer dokumentu
        """
        date = date or datetime.now()
        year = date.year
        month = date.month

        sequence, created = DocumentSequence.objects.select_for_update().get_or_create(
            company_code=company_code,
            document_type=document_type,
            warehouse_number=warehouse_number,
            year=year,
            month=month,
            defaults={'last_number': 0}
        )

        # Zwiększ numer sekwencji
        sequence.last_number += 1
        sequence.save()

        # Format numeru dokumentu
        warehouse_part = f"/{warehouse_number}" if warehouse_number else ""
        document_number = f"{company_code}/{document_type}{warehouse_part}/{year}/{month:02d}/{sequence.last_number:04d}"

        return document_number
