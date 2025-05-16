# Poprawiony plik forms.py
from django import forms
from django.core.validators import FileExtensionValidator
from .models import Product, ProductCategory, Brand, ProductImage


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'slug', 'description', 'parent', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wykluczenie bieżącej kategorii i jej dzieci z listy możliwych kategorii nadrzędnych
        if self.instance.pk:
            self.fields['parent'].queryset = ProductCategory.objects.exclude(
                pk__in=[self.instance.pk] +
                [c.pk for c in self.instance.children.all()]
            )


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'slug', 'description', 'is_active']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'altum_id', 'sku', 'ean', 'name', 'type',
            'description', 'category', 'brand', 'unit', 'vat_rate', 'cn_code',
            'weight', 'height', 'width', 'depth',
            'is_active', 'is_featured'
        ]
        # Jawne ustawienie widgetów dla niektórych pól
        widgets = {
            # Pola wyboru - z wykorzystaniem form-select
            'type': forms.Select(attrs={'class': 'form-select'}),
            'vat_rate': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            # Pola liczbowe z krokiem
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'depth': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtruj aktywne kategorie i marki
        if 'category' in self.fields:
            self.fields['category'].queryset = ProductCategory.objects.all()
            self.fields['category'].empty_label = "- Wybierz kategorię -"

        if 'brand' in self.fields:
            self.fields['brand'].queryset = Brand.objects.all()
            self.fields['brand'].empty_label = "- Wybierz markę -"

        # Dodanie klas CSS do pól tekstowych i tekstowych obszarów
        for field_name, field in self.fields.items():
            css_class = None

            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.NumberInput)):
                css_class = 'form-control'
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'

            if css_class and 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': css_class})


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'is_primary', 'order']
        widgets = {
            'order': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def clean_image(self):
        """Dodatkowa walidacja obrazu - validator kompresji już działa na poziomie modelu"""
        image = self.cleaned_data.get('image')
        if image:
            # Można tu dodać dodatkową walidację, ale kompresja jest już obsługiwana przez validator modelu
            return image
        return image

# Formularz do dodawania wielu zdjęć naraz
