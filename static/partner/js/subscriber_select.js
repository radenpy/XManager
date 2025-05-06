/**
 * Skrypt do obsługi listy powiązanych emaili (subskrybentów)
 */
document.addEventListener('DOMContentLoaded', function () {
    /**
     * Obsługa formularza wyboru emaili
     */
    const emailContactsSelect = document.getElementById('id_email_contacts');

    if (emailContactsSelect) {
        // Inicjalizacja Select2 dla pola emaili
        $(emailContactsSelect).select2({
            placeholder: 'Wyszukaj po e-mailu, imieniu lub nazwisku...',
            allowClear: true,
            tags: true,
            maximumSelectionLength: 10, // Maksymalnie 10 emaili
            ajax: {
                url: document.body.dataset.subscriberLookupUrl || 'partner/api/subscribers/lookup/',
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        search: params.term,
                        page: params.page || 1
                    };
                },
                processResults: function (data, params) {
                    params.page = params.page || 1;

                    return {
                        results: data.results.map(function (item) {
                            return {
                                id: item.id,
                                text: item.email,
                                full_name: item.first_name + ' ' + item.last_name
                            };
                        }),
                        pagination: {
                            more: data.has_more
                        }
                    };
                },
                cache: true
            },
            templateResult: formatSubscriberResult,
            templateSelection: formatSubscriberSelection,
            createTag: function (params) {
                const term = $.trim(params.term);

                // Walidacja emaila
                if (!isValidEmail(term)) {
                    return null;
                }

                return {
                    id: term,
                    text: term,
                    newTag: true
                };
            }
        });

        // Listener na zmianę liczby wybranych emaili
        $(emailContactsSelect).on('change', function () {
            const selectedCount = $(this).val().length;

            // Jeśli przekroczono limit 10 emaili
            if (selectedCount > 10) {
                showMessage('error', 'Można wybrać maksymalnie 10 adresów email.');

                // Usuń ostatnio dodany email
                const values = $(this).val();
                values.pop();
                $(this).val(values).trigger('change');
            }
        });
    }

    /**
     * Formatowanie wyników w dropdownie Select2
     */
    // function formatSubscriberResult(subscriber) {
    //     if (subscriber.loading) {
    //         return subscriber.text;
    //     }

    //     if (subscriber.newTag) {
    //         return $(`
    //             <div class="new-email-option">
    //                 <i class="fas fa-plus-circle me-2"></i> 
    //                 Dodaj nowy email: <strong>${subscriber.text}</strong>
    //             </div>
    //         `);
    //     }

    //     let markup = `
    //         <div class="subscriber-result">
    //             <div class="subscriber-email">${subscriber.text}</div>`;

    //     if (subscriber.full_name && subscriber.full_name.trim() !== '') {
    //         markup += `<div class="subscriber-name text-muted small">${subscriber.full_name}</div>`;
    //     }

    //     markup += '</div>';

    //     return $(markup);
    // }
    function formatSubscriberResult(subscriber) {
        if (subscriber.loading) {
            return subscriber.text;
        }

        if (subscriber.newTag) {
            return $(`
                <div class="new-email-option">
                    <i class="fas fa-plus-circle me-2"></i> 
                    Dodaj nowy email: <strong>${subscriber.text}</strong>
                </div>
            `);
        }

        let markup = `
            <div class="subscriber-result">
                <div class="subscriber-email"><strong>${subscriber.text}</strong></div>`;

        if (subscriber.full_name && subscriber.full_name.trim() !== ' ') {
            markup += `<div class="subscriber-name text-muted small">${subscriber.full_name}</div>`;
        }

        markup += '</div>';

        return $(markup);
    }

    function formatSubscriberSelection(subscriber) {
        if (subscriber.full_name && subscriber.full_name.trim() !== ' ') {
            return `${subscriber.text} (${subscriber.full_name})`;
        }
        return subscriber.text;
    }

    /**
     * Walidacja poprawności adresu email
     */
    function isValidEmail(email) {
        const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return regex.test(email);
    }

    /**
     * Wyświetlanie komunikatu
     */
    function showMessage(type, text) {
        // Jeśli funkcja jest zdefiniowana w main.js, użyj jej
        if (typeof window.showMessage === 'function') {
            window.showMessage(text, type);
            return;
        }

        // W przeciwnym razie zdefiniuj własną implementację
        const messageContainer = document.getElementById('messages-container') || createMessageContainer();

        const message = document.createElement('div');
        message.classList.add('alert', `alert-${type === 'error' ? 'danger' : type}`);
        message.textContent = text;

        // Dodaj przycisk zamknięcia
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.classList.add('btn-close');
        closeButton.dataset.bsDismiss = 'alert';
        closeButton.setAttribute('aria-label', 'Close');

        message.appendChild(closeButton);
        messageContainer.appendChild(message);

        // Automatycznie ukryj komunikat po 5 sekundach
        setTimeout(() => {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 5000);
    }

    /**
     * Funkcja do tworzenia kontenera na komunikaty
     */
    function createMessageContainer() {
        const container = document.createElement('div');
        container.id = 'messages-container';
        container.classList.add('messages-container');
        document.body.appendChild(container);
        return container;
    }
});

/**
 * Style dla formatowania opcji subskrybenta
 */
document.addEventListener('DOMContentLoaded', function () {
    // Dodanie stylów CSS
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .subscriber-result {
            padding: 5px 0;
        }
        
        .subscriber-email {
            font-weight: 500;
        }
        
        .subscriber-name {
            font-size: 0.85em;
            color: #6c757d;
        }
        
        .new-email-option {
            color: #28a745;
            font-weight: 500;
            padding: 5px 0;
        }
        
        .select2-container--default .select2-results__option--highlighted .new-email-option {
            color: white;
        }
    `;

    document.head.appendChild(styleElement);
});