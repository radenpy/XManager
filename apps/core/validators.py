from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image as PILImage
from io import BytesIO
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re
import sys


# Walidator numeru NIP
def validate_nip(value):
    # Usuwamy ewentualne myślniki czy spacje
    value = ''.join(c for c in value if c.isdigit())

    # Sprawdzenie długości
    if len(value) != 10:
        raise ValidationError("NIP musi składać się z 10 cyfr.")

    # Sprawdzenie, czy wszystkie znaki to cyfry
    if not value.isdigit():
        raise ValidationError("NIP może zawierać tylko cyfry.")

    # Wagi używane do obliczania sumy kontrolnej NIP
    weights = (6, 5, 7, 2, 3, 4, 5, 6, 7)

    # Obliczanie sumy kontrolnej
    check_sum = sum(int(value[i]) * weights[i] for i in range(9))
    check_sum %= 11

    # Jeśli suma kontrolna nie zgadza się z ostatnią cyfrą
    if check_sum != int(value[9]):
        raise ValidationError(
            "NIP jest nieprawidłowy - błędna suma kontrolna.")

# Walidator numeru REGON (zarówno 9 jak i 14 cyfr)


def validate_regon(value):
    # Usuwamy ewentualne myślniki czy spacje
    value = ''.join(c for c in value if c.isdigit())

    # Sprawdzenie długości - REGON może mieć 9 lub 14 cyfr
    if len(value) != 9 and len(value) != 14:
        raise ValidationError("REGON musi składać się z 9 lub 14 cyfr.")

    # Sprawdzenie, czy wszystkie znaki to cyfry
    if not value.isdigit():
        raise ValidationError("REGON może zawierać tylko cyfry.")

    # Walidacja dla REGON 9-cyfrowego
    if len(value) == 9:
        weights = (8, 9, 2, 3, 4, 5, 6, 7)
        check_sum = sum(int(value[i]) * weights[i] for i in range(8))
        check_sum %= 11
        if check_sum == 10:
            check_sum = 0

        # Jeśli suma kontrolna nie zgadza się z ostatnią cyfrą
        if check_sum != int(value[8]):
            raise ValidationError(
                "REGON 9-cyfrowy jest nieprawidłowy - błędna suma kontrolna.")

    # Walidacja dla REGON 14-cyfrowego
    elif len(value) == 14:
        weights = (2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8)
        check_sum = sum(int(value[i]) * weights[i] for i in range(13))
        check_sum %= 11
        if check_sum == 10:
            check_sum = 0

        # Jeśli suma kontrolna nie zgadza się z ostatnią cyfrą
        if check_sum != int(value[13]):
            raise ValidationError(
                "REGON 14-cyfrowy jest nieprawidłowy - błędna suma kontrolna.")


# Walidator KRS
krs_validator = RegexValidator(
    regex=r'^\d{10}$',
    message='KRS musi składać się z 10 cyfr.',
    code='invalid_krs'
)

# Walidator numeru telefonu
phone_number_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Numer telefonu musi być w formacie: '+999999999'. Dozwolone do 15 cyfr."
)

# Funkcja walidująca kod pocztowy


def validate_postal_code(value):
    if not re.match(r'^\d{2}-\d{3}$', value):
        raise ValidationError(
            'Kod pocztowy musi być w formacie XX-XXX.',
            code='invalid_postal_code'
        )

# Walidator rozmiaru zdjęcia


def validate_and_compress_image(image):
    # Limit do 2 MB
    limit_mb = 2
    original_size = image.file.size

    # Jeśli zdjęcie jest mniejsze niż limit, po prostu je zwróć
    if original_size <= limit_mb * 1024 * 1024:
        return image

    # Jeśli jest większe, spróbuj je skompresować
    try:
        # Otwórz obraz przy użyciu PIL
        img = PILImage.open(image)
        original_width, original_height = img.width, img.height

        # Zachowaj oryginalny format
        if img.format == 'PNG':
            format_str = 'PNG'
            content_type = 'image/png'
            # Do PNGów używamy metody optymalizacji zamiast parametru jakości
            temp_io = BytesIO()
            img.save(temp_io, format=format_str, optimize=True)
        else:
            format_str = 'JPEG'
            content_type = 'image/jpeg'

            # Znajdź optymalną jakość kompresji, zaczynając od 90%
            # i obniżając maksymalnie o 20% (do 70%)
            quality = 90
            min_quality = 70  # Nie obniżaj jakości poniżej 70%
            temp_io = BytesIO()

            # Najpierw spróbuj z jakością 90%
            img.save(temp_io, format=format_str,
                     quality=quality, optimize=True)
            size = temp_io.tell()

            # Jeśli nadal za duży, stopniowo obniżaj jakość
            while size > limit_mb * 1024 * 1024 and quality > min_quality:
                quality -= 5  # Zmniejsz jakość o 5 punktów
                temp_io = BytesIO()
                img.save(temp_io, format=format_str,
                         quality=quality, optimize=True)
                size = temp_io.tell()

        # Sprawdź końcowy rozmiar
        compressed_size = temp_io.tell()

        # Jeśli nadal przekracza rozmiar, daj jasny komunikat
        if compressed_size > limit_mb * 1024 * 1024:
            raise ValidationError(_(
                f"Zdjęcie jest zbyt duże i nie może być wystarczająco skompresowane "
                f"bez utraty jakości. Obecny rozmiar: {original_size/1024/1024:.2f} MB. "
                f"Spróbuj użyć innego narzędzia do zmniejszenia rozmiaru pliku poniżej {limit_mb} MB "
                f"lub zmniejsz wymiary obrazu."
            ))

        # Przygotuj skompresowany obraz do zwrócenia
        temp_io.seek(0)
        new_image = InMemoryUploadedFile(
            temp_io,
            'ImageField',
            image.name,
            content_type,
            sys.getsizeof(temp_io),
            None
        )

        # Załącz metadane o kompresji
        new_image.compression_info = {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': round((1 - compressed_size/original_size) * 100, 2),
            'dimensions': f"{original_width}x{original_height}",
            'quality': quality if format_str == 'JPEG' else 'optimized'
        }

        return new_image

    except Exception as e:
        # Jeśli coś pójdzie nie tak, wyrzuć standardowy błąd walidacji
        raise ValidationError(
            _(f"Błąd podczas przetwarzania obrazu: {str(e)}"))
