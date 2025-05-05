from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'sku',
            'ean',
            'name',
            'description'
        ]


class RawProductForm(forms.Form):
    ean = forms.CharField()
    name = forms.CharField(label="", widget=forms.TextInput(
        attrs={"placeholder": "Your title"}))
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "new-class-name two",
                "id": "my-id-for-text-area",
                "rows": 10,
                "columns": 20
            }))
