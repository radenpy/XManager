from django import forms
from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name',
            'code',
            'tax_id',
            'tax_id_prefix',
            'regon',
            'krs',
            'street_name',
            'building_number',
            'appartment_number',
            'city',
            'post_code',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'np. ABC'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bez myślników i spacji'}),
            'tax_id_prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'regon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bez myślników i spacji'}),
            'krs': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bez myślników i spacji'}),
            'street_name': forms.TextInput(attrs={'class': 'form-control'}),
            'building_number': forms.TextInput(attrs={'class': 'form-control'}),
            'appartment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'post_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Format: 00-000'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
