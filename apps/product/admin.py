from django.contrib import admin
from .models import Product, ProductCategory, Brand, ProductImage


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("ean", "name", "unit", "vat_rate", "is_active")
    search_fields = ("ean", "name")


# product/admin.py


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image', 'is_primary',
                    'compression_display', 'created_at')
    list_filter = ('is_primary', 'product__category')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('compression_display', 'original_size', 'compressed_size',
                       'compression_ratio', 'compression_quality')

    def compression_display(self, obj):
        """Wyświetla informacje o kompresji w panelu administracyjnym"""
        if obj.compression_ratio:
            return obj.compression_info_display
        return "Bez kompresji"

    compression_display.short_description = "Informacje o kompresji"
