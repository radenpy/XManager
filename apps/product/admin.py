from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("ean", "name", "unit", "vat_rate", "is_active")
    search_fields = ("ean", "name")
