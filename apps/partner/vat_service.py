# vat_service.py
import requests
from django.utils import timezone


class VATService:
    """Serwis do komunikacji z API Wykazu Podatników VAT"""

    BASE_URL = "https://wl-api.mf.gov.pl/api/search"

    @staticmethod
    def verify_vat(nip):
        """Weryfikacja statusu VAT po numerze NIP"""
        try:
            # Usunięcie znaków formatujących z NIP
            nip = ''.join(c for c in nip if c.isdigit())

            # Aktualna data w formacie YYYY-MM-DD
            today = timezone.now().strftime('%Y-%m-%d')

            # Wywołanie API
            url = f"{VATService.BASE_URL}/nip/{nip}?date={today}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Sprawdzenie, czy podmiot istnieje w wykazie
                if 'result' in data and 'subject' in data['result']:
                    subject = data['result']['subject']

                    # Ekstrakcja danych
                    result = {
                        'name': subject.get('name', ''),
                        'nip': subject.get('nip', ''),
                        'status_vat': subject.get('statusVat'),
                        'regon': subject.get('regon', ''),
                        'pesel': subject.get('pesel', None),
                        'krs': subject.get('krs', None),
                        'residence_address': subject.get('residenceAddress', None),
                        'working_address': subject.get('workingAddress', None),
                        'has_virtual_accounts': subject.get('hasVirtualAccounts', False),
                        'accounts': subject.get('accountNumbers', []),
                        'registration_legal_date': subject.get('registrationLegalDate', None),
                        'registration_denial_basis': subject.get('registrationDenialBasis', None),
                        'restoration_basis': subject.get('restorationBasis', None),
                        'restoration_date': subject.get('restorationDate', None),
                        'removal_basis': subject.get('removalBasis', None),
                        'removal_date': subject.get('removalDate', None),
                        'verification_id': data['result'].get('requestId', None),
                    }

                    # Parsowanie adresu
                    if result['working_address']:
                        address_parts = VATService._parse_address(
                            result['working_address'])
                        result.update(address_parts)

                    return True, result, "Podmiot odnaleziony w bazie VAT", result['verification_id']
                else:
                    return False, None, "Podmiot nie został znaleziony w bazie VAT", None
            else:
                return False, None, f"Błąd API: {response.status_code}", None

        except Exception as e:
            return False, None, f"Wystąpił błąd: {str(e)}", None

    @staticmethod
    def _parse_address(address_string):
        """Parsowanie adresu z API MF"""
        result = {
            'street_name': '',
            'building_number': '',
            'apartment_number': '',
            'postal_code': '',
            'city': ''
        }

        if not address_string:
            return result

        try:
            # Typowy format: "ULICA NUMER, KOD MIASTO"
            parts = address_string.split(',')

            # Adres ulicy i numer
            if len(parts) > 0:
                street_parts = parts[0].strip().split(' ')
                if len(street_parts) > 1:
                    # Ostatni element to prawdopodobnie numer
                    result['building_number'] = street_parts[-1]
                    # Reszta to nazwa ulicy
                    result['street_name'] = ' '.join(street_parts[:-1])
                else:
                    result['street_name'] = parts[0].strip()

            # Kod pocztowy i miasto
            if len(parts) > 1:
                city_parts = parts[1].strip().split(' ')
                if len(city_parts) > 1 and VATService._is_postal_code(city_parts[0]):
                    result['postal_code'] = city_parts[0]
                    result['city'] = ' '.join(city_parts[1:])
                else:
                    result['city'] = parts[1].strip()

        except Exception:
            # W przypadku błędu zwracamy oryginalny adres jako nazwę ulicy
            result['street_name'] = address_string

        return result

    @staticmethod
    def _is_postal_code(text):
        """Sprawdzenie, czy tekst jest kodem pocztowym"""
        return len(text) == 6 and text[2] == '-'
