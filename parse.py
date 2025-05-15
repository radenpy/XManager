import re
import openpyxl


def parse_email_list(text):
    # Dzielimy tekst po przecinkach
    entries = [entry.strip() for entry in text.split(',')]
    results = []

    for entry in entries:
        # Sprawdzamy, czy mamy format "Nazwa <email>"
        named_email_match = re.search(r'(.*?)\s*<([^>]+)>', entry)

        if named_email_match:
            full_name = named_email_match.group(1).strip()
            email = named_email_match.group(2).strip()

            # Usuwamy znaki cudzysłowu, jeśli istnieją
            full_name = re.sub(r'^["\'\\s]+|["\'\\s]+$', '', full_name)

            # Sprawdzamy, czy nazwa nie jest emailem
            if '@' in full_name:
                first_name = ''
                last_name = ''
            else:
                # Dzielimy pełne imię na imię i nazwisko
                name_parts = full_name.split()
                if len(name_parts) > 0:
                    first_name = name_parts[0]  # Pierwsze słowo jako imię
                    last_name = ' '.join(name_parts[1:]) if len(
                        name_parts) > 1 else ''  # Reszta jako nazwisko
                else:
                    first_name = ''
                    last_name = ''

            results.append({
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
        else:
            # Jeśli nie ma formatu "Nazwa <email>", próbujemy wyodrębnić sam email
            email_match = re.search(
                r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)', entry)
            if email_match:
                results.append({
                    'email': email_match.group(1),
                    'first_name': '',
                    'last_name': ''
                })

    return results


# Ścieżka do pliku wejściowego i wyjściowego
input_file = '/Users/rafal/Desktop/crmwyciek.txt'
output_file = '/Users/rafal/Desktop/crmwyciek-parse.xlsx'

# Odczytujemy zawartość pliku
with open(input_file, 'r', encoding='utf-8') as file:
    content = file.read()

# Parsujemy zawartość
parsed_data = parse_email_list(content)

# Tworzymy nowy plik Excel
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet.title = "Adresy Email"

# Dodajemy nagłówki
sheet['A1'] = "Email"
sheet['B1'] = "Imię"
sheet['C1'] = "Nazwisko"

# Dodajemy dane
# Zaczynamy od wiersza 2 (po nagłówkach)
for i, item in enumerate(parsed_data, start=2):
    sheet[f'A{i}'] = item['email']
    sheet[f'B{i}'] = item['first_name']
    sheet[f'C{i}'] = item['last_name']

# Dostosowujemy szerokość kolumn do zawartości
sheet.column_dimensions['A'].width = 40
sheet.column_dimensions['B'].width = 20
sheet.column_dimensions['C'].width = 25

# Zapisujemy plik Excel
workbook.save(output_file)

print(
    f"Przetwarzanie zakończone. Wyniki zapisano w pliku Excel: {output_file}")
