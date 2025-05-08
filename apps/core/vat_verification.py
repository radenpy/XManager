from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.validators import validate_nip
import xml.etree.ElementTree as ET
from io import StringIO
import logging
import requests

logger = logging.getLogger(__name__)

# Kraje UE - przydatne do weryfikacji w API VIES
EU_COUNTRY_CODES = [
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
    'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
    'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
]


class VATVerificationService:
    """
    Serwis do weryfikacji numerów VAT w różnych API
    """
    @staticmethod
    def get_verification_api(country_code):
        """Zwraca odpowiednie API do weryfikacji VAT w zależności od kraju"""

        if country_code == 'PL':
            return 'poland_vat_api'
        elif country_code in EU_COUNTRY_CODES:
            return 'vies_vat_api'
        else:
            return {'status': 'not available', 'message': 'Country outside EU. VAT verification unavailable.'}

    @staticmethod
    def verify_vat(country_code, vat_number):
        """
        Weryfikuje numer VAT w odpowiednim API i zwraca dane
        """
        api_type = VATVerificationService.get_verification_api(country_code)
        success = False
        message = ""
        data = None
        verification_id = None

        try:
            if isinstance(api_type, dict) and api_type.get('status') == 'not available':
                # Zwracamy informację, że weryfikacja nie jest dostępna
                return False, None, api_type.get('message', "Brak dostępnego API do weryfikacji."), None

            elif api_type == 'poland_vat_api':
                success, data, message, verification_id = VATVerificationService._verify_polish_vat(
                    vat_number)
            elif api_type == 'vies_vat_api':
                success, data, message, verification_id = VATVerificationService._verify_eu_vat(
                    country_code, vat_number)
            else:
                message = "Brak dostępnego API do weryfikacji numerów VAT."
                return False, None, message, None

            return success, data, message, verification_id

        except Exception as e:
            logger.exception(f"Błąd podczas weryfikacji VAT: {str(e)}")
            return False, None, str(e), None

    @staticmethod
    def _verify_polish_vat(vat_number):
        """
        Weryfikacja polskiego numeru NIP w API Ministerstwa Finansów
        """
        try:
            # Usuń wszystkie znaki specjalne
            vat_number = ''.join(c for c in vat_number if c.isdigit())

            validate_nip(vat_number)

            # Wywołanie API Ministerstwa Finansów
            url = f"https://wl-api.mf.gov.pl/api/search/nip/{vat_number}?date={timezone.now().strftime('%Y-%m-%d')}"
            headers = {'Accept': 'application/json'}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Sprawdź czy podmiot istnieje
                if not data.get('result', {}).get('subject'):
                    return False, None, "Nie znaleziono podmiotu o podanym numerze NIP.", None

                subject = data.get('result', {}).get('subject', {})

                # Pobieranie identyfikatora weryfikacji
                verification_id = data.get('result', {}).get('requestId')

                # Parsowanie adresu - w API MF adres jest pojedynczym stringiem
                working_address = subject.get('workingAddress', '')

                # Próba rozparsowania adresu
                city = ''
                street_name = ''
                building_number = ''
                postal_code = ''

                # Typowy format: "ULICA NUMER, KOD MIASTO"
                if working_address:
                    try:
                        address_parts = working_address.split(',')

                        # Część z ulicą i numerem
                        if len(address_parts) > 0:
                            street_parts = address_parts[0].strip().split(' ')
                            if len(street_parts) > 1:
                                # Ostatni element to numer
                                building_number = street_parts[-1]
                                # Reszta to nazwa ulicy
                                street_name = ' '.join(street_parts[:-1])
                            else:
                                street_name = address_parts[0].strip()

                        # Część z kodem i miastem
                        if len(address_parts) > 1:
                            city_parts = address_parts[1].strip().split(' ')
                            if len(city_parts) > 1:
                                # Pierwszy element to kod pocztowy
                                postal_code = city_parts[0]
                                # Reszta to nazwa miasta
                                city = ' '.join(city_parts[1:])
                    except Exception as e:
                        print(f"Błąd parsowania adresu: {str(e)}")

                # Pobieranie danych firmy
                partner_data = {
                    'name': subject.get('name', ''),
                    'city': city,
                    'street_name': street_name,
                    'building_number': building_number,
                    'postal_code': postal_code,
                }

                # Formatowanie danych - bez warunku 'if success and data', bo success nie jest zdefiniowane
                for field in ['name', 'city', 'street_name']:
                    if field in partner_data and partner_data[field]:
                        # Konwersja na title case (pierwszy znak każdego słowa wielki)
                        partner_data[field] = partner_data[field].lower(
                        ).capitalize()

                return True, partner_data, "Numer VAT został zweryfikowany pomyślnie.", verification_id
            else:
                return False, None, f"Nie udało się zweryfikować numeru NIP. Kod odpowiedzi: {response.status_code}", None

        except ValidationError as e:
            return False, None, str(e), None
        except requests.RequestException as e:
            return False, None, f"Błąd komunikacji z API Ministerstwa Finansów: {str(e)}", None
        except Exception as e:
            print(f"Niespodziewany błąd: {str(e)}")
            return False, None, str(e), None

    @staticmethod
    def _verify_eu_vat(country_code, vat_number):
        """
        Weryfikacja numeru VAT w API VIES (dla krajów UE)
        """
        try:
            # Wywołanie API VIES
            url = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"
            headers = {'Content-Type': 'text/xml;charset=UTF-8'}

            # Przygotowanie zapytania SOAP z poprawnym namespace
            data = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
                        xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
                <soapenv:Header/>
                <soapenv:Body>
                    <urn:checkVat>
                        <urn:countryCode>{country_code}</urn:countryCode>
                        <urn:vatNumber>{vat_number}</urn:vatNumber>
                    </urn:checkVat>
                </soapenv:Body>
            </soapenv:Envelope>
            """

            # Dodaj logowanie do debugowania
            print(f"Wysyłanie zapytania VIES: {url}")
            print(f"Treść zapytania: {data[:200]}...")

            response = requests.post(
                url, headers=headers, data=data, timeout=15)

            # Logowanie odpowiedzi
            print(f"Odpowiedź API (status: {response.status_code})")
            print(f"Nagłówki odpowiedzi: {response.headers}")
            print(f"Treść odpowiedzi: {response.text[:300]}...")

            if response.status_code == 200:
                print(f"Pełna odpowiedź API VIES: {response.text}")
                # Sprawdzenie czy numer VAT jest poprawny - bardziej elastyczny warunek
                valid_patterns = [
                    "valid>true<", "<valid>true</valid>", "<ns2:valid>true</ns2:valid>"]
                is_valid = any(
                    pattern in response.text for pattern in valid_patterns)

                if is_valid:

                    # Sprawdzenie czy numer VAT jest poprawny
                    if "valid>true<" in response.text:
                        # Parsowanie XML
                        try:
                            # Usuwanie namespace dla łatwiejszego parsowania
                            xml_text = response.text.replace('soap:', '')

                            # Parsowanie XML
                            from xml.etree import ElementTree as ET
                            root = ET.fromstring(xml_text)

                            # Wyciąganie danych
                            name = ''
                            address = ''
                            verification_id = None

                            for elem in root.iter():
                                if 'name' in elem.tag.lower():
                                    name = elem.text.strip() if elem.text else ''
                                elif 'address' in elem.tag.lower():
                                    address = elem.text.strip() if elem.text else ''
                                elif 'requestIdentifier' in elem.tag.lower():
                                    verification_id = elem.text.strip() if elem.text else ''

                            # Podział adresu na części
                            city = ''
                            street = ''
                            building_number = ''
                            postal_code = ''

                            if address:
                                address_parts = address.split('\n')
                                if len(address_parts) >= 1:
                                    street = address_parts[0]
                                    # Próba pobrania numeru budynku z nazwy ulicy
                                    street_parts = street.split(' ')
                                    if len(street_parts) > 1 and any(char.isdigit() for char in street_parts[-1]):
                                        building_number = street_parts[-1]
                                        street = ' '.join(street_parts[:-1])

                                if len(address_parts) >= 2:
                                    city_line = address_parts[1]
                                    city_parts = city_line.split(' ')
                                    if len(city_parts) >= 2:
                                        # Sprawdź, czy pierwszy element wygląda jak kod pocztowy
                                        if any(char.isdigit() for char in city_parts[0]):
                                            postal_code = city_parts[0]
                                            city = ' '.join(city_parts[1:])
                                        else:
                                            city = city_line

                            # Pobieranie danych firmy
                            partner_data = {
                                'name': name,
                                'city': city,
                                'street_name': street,
                                'building_number': building_number,
                                'postal_code': postal_code,
                                'apartment_number': '',  # Dodaj puste pole dla apartamentu
                            }

                            print(
                                f"Przetworzone dane partnera: {partner_data}")

                            return True, partner_data, "Numer VAT został zweryfikowany pomyślnie.", verification_id

                        except Exception as parse_error:
                            print(
                                f"Błąd podczas parsowania XML: {str(parse_error)}")
                            return False, None, f"Błąd podczas przetwarzania odpowiedzi XML: {str(parse_error)}", None
                    else:
                        return False, None, "Nieprawidłowy numer VAT.", None
                else:
                    return False, None, f"Nie udało się zweryfikować numeru VAT. Kod odpowiedzi: {response.status_code}", None
        except requests.RequestException as e:
            print(f"Błąd zapytania HTTP: {str(e)}")
            return False, None, f"Błąd komunikacji z API VIES: {str(e)}", None
        except Exception as e:
            print(f"Niespodziewany błąd: {str(e)}")
            return False, None, f"Błąd podczas przetwarzania odpowiedzi: {str(e)}", None
