from django.db import models


class VATRate(models.TextChoices):
    ZERO = "0", "0%"
    FIVE = "5", "5%"
    EIGHT = "8", "8%"
    TWENTY_THREE = "23", "23%"
    NP = "NP", "Nie podlega"
    ZW = "ZW", "Zwolniony"


class Product(models.Model):
    sku = models.CharField("Indeks", max_length=50, unique=True)
    ean = models.CharField("EAN", max_length=13, unique=True)
    name = models.CharField("Nazwa artykułu", max_length=255)
    description = models.CharField("Opis", max_length=1000, null=True)
    type = models.CharField("Type", max_length=10)
    unit = models.CharField("Jednostka", max_length=10, default="szt")
    vat_rate = models.CharField(
        "Stawka VAT",
        max_length=5,
        choices=VATRate.choices,
        default=VATRate.TWENTY_THREE
    )
    is_active = models.BooleanField("Aktywny", default=True)

    def __str__(self):
        return f"{self.ean} - {self.name}"
