# product/models.py
from django.db import models
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from apps.core.models import CoreModel
from apps.core.validators import validate_and_compress_image


class VATRate(models.TextChoices):
    ZERO = "0", "0%"
    FIVE = "5", "5%"
    EIGHT = "8", "8%"
    TWENTY_THREE = "23", "23%"
    NP = "NP", "Nie podlega"
    ZW = "ZW", "Zwolniony"


class ProductCategory(CoreModel):
    """Model kategorii produktów"""
    name = models.CharField("Nazwa kategorii", max_length=100)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Opis", blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        verbose_name="Kategoria nadrzędna",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children"
    )
    is_active = models.BooleanField("Aktywna", default=True)

    class Meta:
        verbose_name = "Kategoria produktu"
        verbose_name_plural = "Kategorie produktów"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:category_detail', kwargs={'slug': self.slug})


class Brand(CoreModel):
    """Model producenta/marki"""
    name = models.CharField("Nazwa producenta", max_length=100)
    slug = models.SlugField("Slug", unique=True)
    description = models.TextField("Opis", blank=True, null=True)
    is_active = models.BooleanField("Aktywny", default=True)

    class Meta:
        verbose_name = "Marka"
        verbose_name_plural = "Marki"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:brand_detail', kwargs={'slug': self.slug})


# Zmienione na dziedziczenie z CoreModel
class Product(CoreModel):
    """Model produktu rozszerzony o dodatkowe funkcjonalności"""
    MARKET_TYPE_CHOICES = (
        ('ND', 'ND'),
        ('ND-EU', 'ND-EU'),
        ('D', 'D'),
        ('V', 'V'),
        (' ', ' '),
    )

    # Istniejące pola z migracji
    id = models.BigAutoField(
        auto_created=True, primary_key=True, verbose_name='ID')
    sku = models.CharField("Indeks", max_length=50, unique=True)
    ean = models.CharField("EAN", max_length=13, unique=True)
    name = models.CharField("Nazwa artykułu", max_length=255)
    # Istniejące pole, nie zmieniaj na 'market_type'
    type = models.CharField(
        "Typ rynku",
        max_length=10,
        choices=MARKET_TYPE_CHOICES,
        default=' '
    )
    unit = models.CharField("Jednostka", max_length=10, default="szt")
    vat_rate = models.CharField(
        "Stawka VAT",
        max_length=5,
        choices=VATRate.choices,
        default=VATRate.TWENTY_THREE
    )
    description = models.CharField(
        "Opis", max_length=1000, null=True)  # Istniejące pole
    is_active = models.BooleanField("Aktywny", default=True)

    # Nowe pola do dodania w nowej migracji
    # Dodaj null=True i blank=True
    altum_id = models.CharField(
        "Altum ID", max_length=50, unique=True, null=True, blank=True)
    category = models.ForeignKey(
        ProductCategory,
        verbose_name="Kategoria",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )
    brand = models.ForeignKey(
        Brand,
        verbose_name="Marka",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # Dodane pole kodu CN (Combined Nomenclature)
    cn_code = models.CharField(
        "Kod CN",
        max_length=10,  # Standardowe kody CN mają 8 cyfr, ale dodaję zapas
        blank=True,
        null=True,
        help_text="Kod CN (Combined Nomenclature) używany do celów celnych w UE"
    )

    # Pola fizycznych wymiarów
    weight = models.DecimalField(
        "Waga (kg)",
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True
    )
    height = models.DecimalField(
        "Wysokość (cm)",
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    width = models.DecimalField(
        "Szerokość (cm)",
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )
    depth = models.DecimalField(
        "Głębokość (cm)",
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True
    )

    is_featured = models.BooleanField("Wyróżniony", default=False)

    # Pola created_at i updated_at są już dostępne z CoreModel

    class Meta:
        verbose_name = "Produkt"
        verbose_name_plural = "Produkty"
        ordering = ['name']

    def __str__(self):
        return f"{self.sku} - {self.name}"

    def get_absolute_url(self):
        return reverse('product:product_detail', kwargs={'pk': self.pk})


class ProductImage(CoreModel):
    """Model obrazka produktu"""
    product = models.ForeignKey(
        Product,
        verbose_name="Produkt",
        on_delete=models.CASCADE,
        related_name="images"
    )

    # Pole obrazu z walidatorem kompresji
    image = models.ImageField(
        "Zdjęcie",
        upload_to="products/%Y/%m/",
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']),
            validate_and_compress_image
        ]
    )

    # Standardowe pola
    alt_text = models.CharField(
        "Tekst alternatywny", max_length=255, blank=True, null=True)
    is_primary = models.BooleanField("Główne zdjęcie", default=False)
    order = models.PositiveIntegerField("Kolejność", default=0)

    # Pola do przechowywania informacji o kompresji
    original_size = models.PositiveIntegerField(
        "Oryginalny rozmiar (bytes)", null=True, blank=True)
    compressed_size = models.PositiveIntegerField(
        "Skompresowany rozmiar (bytes)", null=True, blank=True)
    compression_ratio = models.FloatField(
        "Stopień kompresji (%)", null=True, blank=True)
    compression_quality = models.CharField(
        "Jakość kompresji", max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = "Zdjęcie produktu"
        verbose_name_plural = "Zdjęcia produktów"
        ordering = ['order', 'is_primary']

    def __str__(self):
        return f"Zdjęcie produktu {self.product.name}"

    def save(self, *args, **kwargs):
        """Zapisz informacje o kompresji przed zapisaniem modelu"""
        # Jeśli pole image zostało skompresowane, zapisz informacje o kompresji
        if hasattr(self.image, 'compression_info'):
            info = self.image.compression_info
            self.original_size = info['original_size']
            self.compressed_size = info['compressed_size']
            self.compression_ratio = info['compression_ratio']
            self.compression_quality = info.get('quality', 'unknown')

        super().save(*args, **kwargs)

    @property
    def compression_info_display(self):
        """Zwraca sformatowane informacje o kompresji do wyświetlenia"""
        if self.compression_ratio:
            return f"Kompresja: {self.compression_ratio:.1f}% (z {self.original_size/1024:.1f} kB do {self.compressed_size/1024:.1f} kB)"
        return "Bez kompresji"
