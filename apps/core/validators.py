from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re


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
