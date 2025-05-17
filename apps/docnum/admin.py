# apps/docnum/admin.py

from django.contrib import admin
from .models import DocumentSequence


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ('company_code', 'document_type',
                    'warehouse_number', 'year', 'month', 'last_number')
    list_filter = ('company_code', 'document_type', 'year', 'month')
    search_fields = ('company_code', 'document_type', 'warehouse_number')
