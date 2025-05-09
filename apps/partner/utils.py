from django.conf import settings
from django_countries import countries

# Słownik tłumaczeń nazw krajów na język polski
COUNTRY_TRANSLATIONS = {
    'Poland': 'Polska',
    'Germany': 'Niemcy',
    'France': 'Francja',
    'Spain': 'Hiszpania',
    'Italy': 'Włochy',
    'United Kingdom': 'Wielka Brytania',
    'Netherlands': 'Holandia',
    'Belgium': 'Belgia',
    'Sweden': 'Szwecja',
    'Austria': 'Austria',
    'Denmark': 'Dania',
    'Greece': 'Grecja',
    'Finland': 'Finlandia',
    'Portugal': 'Portugalia',
    'Ireland': 'Irlandia',
    'Luxembourg': 'Luksemburg',
    'Czech Republic': 'Czechy',
    'Romania': 'Rumunia',
    'Hungary': 'Węgry',
    'Bulgaria': 'Bułgaria',
    'Slovakia': 'Słowacja',
    'Croatia': 'Chorwacja',
    'Slovenia': 'Słowenia',
    'Lithuania': 'Litwa',
    'Latvia': 'Łotwa',
    'Cyprus': 'Cypr',
    'Estonia': 'Estonia',
    'Malta': 'Malta',
    'United States': 'Stany Zjednoczone',
    'Canada': 'Kanada',
    'China': 'Chiny',
    'Japan': 'Japonia',
    'Russia': 'Rosja',
    'Switzerland': 'Szwajcaria',
    'Norway': 'Norwegia',
    'Australia': 'Australia',
    'Brazil': 'Brazylia',
    'India': 'Indie',
    'Mexico': 'Meksyk',
    'South Korea': 'Korea Południowa',
    'Turkey': 'Turcja',
    'Indonesia': 'Indonezja',
    'South Africa': 'Republika Południowej Afryki',
    'Argentina': 'Argentyna',
    'Saudi Arabia': 'Arabia Saudyjska',
    'Ukraine': 'Ukraina',
    'Israel': 'Izrael',
    'Egypt': 'Egipt',
    'Singapore': 'Singapur',
    'Thailand': 'Tajlandia',
    'Malaysia': 'Malezja',
    'Vietnam': 'Wietnam',
    'New Zealand': 'Nowa Zelandia',
    'Chile': 'Chile',
    'Colombia': 'Kolumbia',
    'Philippines': 'Filipiny',
    'Pakistan': 'Pakistan',
    'Morocco': 'Maroko',
    'Peru': 'Peru',
    'United Arab Emirates': 'Zjednoczone Emiraty Arabskie',
    'Bangladesh': 'Bangladesz',
    'Algeria': 'Algieria',
    'Nigeria': 'Nigeria',
    'Venezuela': 'Wenezuela',
    'Kenya': 'Kenia',
    'Cuba': 'Kuba',
    'Ecuador': 'Ekwador',
    'Uruguay': 'Urugwaj',
    'Costa Rica': 'Kostaryka',
    'Panama': 'Panama',
    'Iceland': 'Islandia',
    'Belarus': 'Białoruś',
    'Serbia': 'Serbia',
    'Georgia': 'Gruzja',
    'Mongolia': 'Mongolia',
    'Qatar': 'Katar',
    'Kuwait': 'Kuwejt',
    'Monaco': 'Monako',
    'Liechtenstein': 'Liechtenstein',
    'Moldova': 'Mołdawia',
    'Paraguay': 'Paragwaj',
}


def get_translated_countries():
    """
    Zwraca listę krajów z django-countries ze spolszczonymi nazwami

    Returns:
        list: Lista krotek (kod_kraju, nazwa_w_języku_polskim)
    """
    translated_countries = []

    # Iterujemy po wszystkich krajach z django-countries
    for code, name in dict(countries).items():
        # Jeśli istnieje tłumaczenie, używamy go
        translated_name = COUNTRY_TRANSLATIONS.get(name, name)
        translated_countries.append((code, translated_name))

    # Przygotuj posortowaną listę krajów
    # 1. Polska na początku
    # 2. Najczęściej wybierane kraje EU posortowane alfabetycznie
    # 3. Pozostałe kraje posortowane alfabetycznie

    # Znajdź i wydziel Polskę
    poland = None
    for country in translated_countries:
        if country[0] == 'PL':
            poland = country
            break

    if poland:
        translated_countries.remove(poland)

    # Najczęściej wybierane kraje UE
    frequently_used = [
        'DE', 'GB', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'CZ', 'SK', 'LT', 'LV', 'EE'
    ]

    freq_countries = []
    remaining_countries = []

    # Podziel kraje na "często używane" i "pozostałe"
    for country in translated_countries:
        code = country[0]
        if code in frequently_used:
            freq_countries.append(country)
        else:
            remaining_countries.append(country)

    # Sortuj alfabetycznie po nazwach
    freq_countries.sort(key=lambda x: x[1])
    remaining_countries.sort(key=lambda x: x[1])

    # Złóż listę z powrotem, zaczynając od Polski
    sorted_countries = []
    if poland:
        sorted_countries.append(poland)
    sorted_countries.extend(freq_countries)
    sorted_countries.extend(remaining_countries)

    return sorted_countries


def add_to_context(context):
    """
    Dodaje przetłumaczone nazwy krajów do kontekstu szablonu

    Args:
        context (dict): Kontekst szablonu Django

    Returns:
        dict: Zaktualizowany kontekst z listą przetłumaczonych krajów
    """
    context['countries'] = get_translated_countries()
    return context
