/**
 * Główny plik JavaScript dla aplikacji XManager
 */
document.addEventListener('DOMContentLoaded', function () {

    // Inicjalizacja tooltipów
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicjalizacja Select2
    initializeSelect2();

    // Obsługa zamykania komunikatów
    initializeAlertDismiss();

    // Obsługa podświetlania aktywnych elementów menu
    highlightActiveMenuItem();

    // Obsługa rozwijania/zwijania sidebara na urządzeniach mobilnych
    handleMobileSidebar();
});

/**
 * Inicjalizacja kontrolek Select2
 */
function initializeSelect2() {
    // Podstawowe ustawienia dla zwykłych selectów
    $('.select2').select2({
        width: '100%',
        theme: 'bootstrap-5',
        placeholder: function () {
            return $(this).data('placeholder') || 'Wybierz opcję';
        },
        allowClear: true
    });

    // Ustawienia dla selectów wielokrotnego wyboru
    $('.select2-multiple').select2({
        width: '100%',
        theme: 'bootstrap-5',
        placeholder: function () {
            return $(this).data('placeholder') || 'Wybierz opcje';
        },
        allowClear: true,
        closeOnSelect: false
    });
}

/**
 * Obsługa zamykania komunikatów
 */
function initializeAlertDismiss() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function (alert) {
        // Automatyczne ukrywanie alertów po 5 sekundach
        setTimeout(function () {
            if (alert && alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
}

/**
 * Podświetlanie aktywnych elementów menu
 */
function highlightActiveMenuItem() {
    // Pobierz aktualny URL
    const currentUrl = window.location.pathname;

    // Znajdź wszystkie linki w menu
    const navLinks = document.querySelectorAll('.nav-link');

    // Przetwórz każdy link
    navLinks.forEach(function (link) {
        const href = link.getAttribute('href');

        // Jeśli href jest aktualnym URL lub jest jego początkiem (dla podstron)
        if (href === currentUrl || (href !== '/' && currentUrl.startsWith(href))) {
            link.classList.add('active');

            // Jeśli link jest w submenu, rozwiń jego rodzica
            const parent = link.closest('.collapse');
            if (parent) {
                parent.classList.add('show');
                const parentTrigger = document.querySelector(`[data-bs-toggle="collapse"][href="#${parent.id}"]`);
                if (parentTrigger) {
                    parentTrigger.setAttribute('aria-expanded', 'true');
                }
            }
        }
    });
}

/**
 * Obsługa rozwijania/zwijania sidebara na urządzeniach mobilnych
 */
function handleMobileSidebar() {
    const toggleSidebarBtn = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('#sidebar');

    if (toggleSidebarBtn && sidebar) {
        toggleSidebarBtn.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }
}

/**
 * Pokazywanie komunikatu
 * @param {string} message - Treść komunikatu
 * @param {string} type - Typ komunikatu (success, danger, warning, info)
 */
function showMessage(message, type = 'info') {
    // Kontener na komunikaty
    let messagesContainer = document.querySelector('.messages-container');

    // Jeśli kontener nie istnieje, stwórz go
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.classList.add('messages-container');
        document.body.appendChild(messagesContainer);
    }

    // Stwórz element komunikatu
    const alertElement = document.createElement('div');
    alertElement.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
    alertElement.setAttribute('role', 'alert');
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Dodaj komunikat do kontenera
    messagesContainer.appendChild(alertElement);

    // Automatyczne ukrycie po 5 sekundach
    setTimeout(function () {
        const bsAlert = new bootstrap.Alert(alertElement);
        bsAlert.close();
    }, 5000);
}

/**
 * Wyświetlanie okna potwierdzenia
 * @param {string} message - Treść komunikatu
 * @param {Function} callback - Funkcja wywoływana po potwierdzeniu
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Format liczby jako waluta
 * @param {number} value - Wartość do sformatowania
 * @param {string} currency - Kod waluty (domyślnie PLN)
 * @returns {string} Sformatowana wartość
 */
function formatCurrency(value, currency = 'PLN') {
    return new Intl.NumberFormat('pl-PL', {
        style: 'currency',
        currency: currency
    }).format(value);
}

/**
 * Format daty
 * @param {string|Date} date - Data do sformatowania
 * @param {boolean} includeTime - Czy dołączyć czas
 * @returns {string} Sformatowana data
 */
function formatDate(date, includeTime = false) {
    const dateObj = new Date(date);
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };

    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }

    return dateObj.toLocaleDateString('pl-PL', options);
}

/**
 * Skopiuj tekst do schowka
 * @param {string} text - Tekst do skopiowania
 * @param {Function} callback - Opcjonalna funkcja wywoływana po skopiowaniu
 */
function copyToClipboard(text, callback) {
    navigator.clipboard.writeText(text).then(function () {
        if (callback) {
            callback(true);
        } else {
            showMessage('Skopiowano do schowka', 'success');
        }
    }).catch(function (err) {
        console.error('Błąd kopiowania do schowka:', err);
        if (callback) {
            callback(false);
        } else {
            showMessage('Nie udało się skopiować do schowka', 'danger');
        }
    });
}