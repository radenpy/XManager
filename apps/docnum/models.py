# apps.docnum

from django.db import models
from django.db import transaction


class DocumentSequence(models.Model):
    """Model do przechowywania sekwencji numerów dokumentów"""
    company_code = models.CharField(max_length=10)
    document_type = models.CharField(max_length=10)
    warehouse_number = models.CharField(max_length=5, blank=True, null=True)
    year = models.IntegerField()
    month = models.IntegerField()
    last_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ('company_code', 'document_type',
                           'warehouse_number', 'year', 'month')
        indexes = [
            models.Index(
                fields=['company_code', 'document_type', 'warehouse_number', 'year', 'month']),
        ]
        verbose_name = "Sekwencja numeracji dokumentów"
        verbose_name_plural = "Sekwencje numeracji dokumentów"

    def __str__(self):
        warehouse_str = f"/{self.warehouse_number}" if self.warehouse_number else ""
        return f"{self.company_code}/{self.document_type}{warehouse_str}/{self.year}/{self.month:02d}"
