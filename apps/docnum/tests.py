# apps/docnum/tests.py

from django.test import TestCase
from .services import DocumentNumberService
from .models import DocumentSequence


class DocumentNumberServiceTestCase(TestCase):
    def test_generate_number(self):
        # Test generowania podstawowego numeru dokumentu
        number = DocumentNumberService.generate_number(
            company_code='ABC',
            document_type='FV'
        )

        # Sprawdź format numeru
        self.assertRegex(number, r'^ABC/FV/\d{4}/\d{2}/\d{4}$')

        # Sprawdź, czy sekwencja została utworzona
        self.assertEqual(DocumentSequence.objects.count(), 1)

        # Sprawdź, czy kolejny numer zwiększa się
        next_number = DocumentNumberService.generate_number(
            company_code='ABC',
            document_type='FV'
        )

        # Sprawdź, czy numer sekwencji zwiększył się o 1
        sequence = DocumentSequence.objects.first()
        self.assertEqual(sequence.last_number, 2)

    def test_generate_warehouse_document_number(self):
        # Test generowania numeru dla dokumentu magazynowego
        number = DocumentNumberService.generate_number(
            company_code='ABC',
            document_type='WZ',
            warehouse_number='01'
        )

        # Sprawdź format numeru
        self.assertRegex(number, r'^ABC/WZ/01/\d{4}/\d{2}/\d{4}$')
