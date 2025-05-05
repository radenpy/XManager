/**
 * Skrypt do walidacji i autouzupełniania danych po numerze VAT
 * Obsługuje django-countries do wyboru kraju
 */
document.addEventListener('DOMContentLoaded', function () {
    // Inicjalizacja tooltipów Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Sprawdź, czy strona zawiera elementy formularza weryfikacji VAT
    const vatInput = document.getElementById('id_vat_number');
    const countrySelect = document.getElementById('id_country');

    if (vatInput && countrySelect) {
        // Dodaj maseczkę do pola numeru VAT
        $(vatInput).on('input', function () {
            // Usuń wszystkie znaki niealfanumeryczne
            this.value = this.value.replace(/[^a-zA-Z0-9]/g, '');
        });

        // Dodaj walidację przed wysłaniem formularza
        const form = vatInput.closest('form');
        if (form) {
            form.addEventListener('submit', function (e) {
                if (!validateVATForm()) {
                    e.preventDefault();
                }
            });
        }
    }

    /**
     * Walidacja formularza VAT
     */
    function validateVATForm() {
        const countryValue = countrySelect.value;
        const vatValue = vatInput.value.trim();

        if (!countryValue) {
            showFormError(countrySelect, 'Wybierz kraj.');
            return false;
        }

        if (!vatValue) {
            showFormError(vatInput, 'Wprowadź numer VAT.');
            return false;
        }

        // Usuń komunikaty o błędach
        clearFormErrors();

        return true;
    }

    /**
     * Wyświetlanie błędu formularza
     */
    function showFormError(element, message) {
        // Usuń istniejące komunikaty
        clearFormError(element);

        // Dodaj klasę błędu
        element.classList.add('is-invalid');

        // Stwórz element z komunikatem
        const errorElement = document.createElement('div');
        errorElement.classList.add('invalid-feedback');
        errorElement.textContent = message;

        // Dodaj komunikat po elemencie
        element.parentNode.appendChild(errorElement);
    }

    /**
     * Usunięcie błędu formularza
     */
    function clearFormError(element) {
        element.classList.remove('is-invalid');

        // Usuń istniejące komunikaty
        const errorElements = element.parentNode.querySelectorAll('.invalid-feedback');
        errorElements.forEach(function (errorElement) {
            errorElement.parentNode.removeChild(errorElement);
        });
    }

    /**
     * Usunięcie wszystkich błędów formularza
     */
    function clearFormErrors() {
        const formControls = document.querySelectorAll('.form-control, .form-select');
        formControls.forEach(function (element) {
            clearFormError(element);
        });
    }

    /**
     * Walidacja numeru VAT dla różnych krajów
     */
    function validateVAT(countryCode, vatNumber) {
        // Usunięcie znaków specjalnych z numeru VAT
        vatNumber = vatNumber.replace(/[^a-zA-Z0-9]/g, '');

        // Walidacja dla Polski
        if (countryCode === 'PL') {
            return validatePolishVAT(vatNumber);
        }

        // Domyślna walidacja dla innych krajów
        return vatNumber.length > 3;
    }

    /**
     * Walidacja polskiego numeru NIP
     */
    function validatePolishVAT(nip) {
        if (nip.length !== 10 || !/^\d+$/.test(nip)) {
            return false;
        }

        // Wagi stosowane do obliczania sumy kontrolnej
        const weights = [6, 5, 7, 2, 3, 4, 5, 6, 7];

        // Obliczenie sumy kontrolnej
        let sum = 0;
        for (let i = 0; i < 9; i++) {
            sum += parseInt(nip.charAt(i)) * weights[i];
        }

        sum %= 11;

        // Porównanie sumy kontrolnej z ostatnią cyfrą NIP
        return sum === parseInt(nip.charAt(9));
    }
});