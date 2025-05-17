# apps/docnum/urls.py

from django.urls import path
from . import api

app_name = 'docnum'

urlpatterns = [
    path('api/generate-number/', api.generate_document_number,
         name='generate_number'),
]
