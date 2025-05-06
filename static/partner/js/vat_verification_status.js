// /**
//  * VAT Verification Status functionality
//  */
// const VATVerificationStatus = {
//     // Ustawienia stronicowania
//     paginationSettings: {
//         itemsPerPage: 10,
//         currentPage: 1,
//         totalPages: 1
//     },
//     /**
//      * Initialize VAT verification status functionality
//      */
//     init: function () {
//         this.initVerifyAgainButton();
//     },

//     /**
//      * Add verification tab to the modal
//      */
//     addVerificationTab: function () {
//         // Check if verification tab already exists
//         if ($('#verification-tab').length > 0) {
//             return;
//         }

//         // Add tab button to the nav
//         $('#partnerTabs').append(`
//             <li class="nav-item" role="presentation">
//                 <button class="nav-link" id="verification-tab" data-bs-toggle="tab" 
//                        data-bs-target="#verification" type="button" role="tab" 
//                        aria-controls="verification" aria-selected="false">
//                     Weryfikacja VAT
//                 </button>
//             </li>
//         `);

//         // Add tab content with new layout
//         $('#partnerTabsContent').append(`
//             <div class="tab-pane fade" id="verification" role="tabpanel" aria-labelledby="verification-tab">
//                 <div class="card border-0">
//                     <div class="card-body">
//                         <div class="mb-4">
//                             <h5 class="mb-3">Aktualny status VAT</h5>

//                             <div class="row mb-3">
//                                 <div class="col-md-6">
//                                     <p><strong>Status:</strong> <span id="verification-status"></span></p>
//                                 </div>
//                                 <div class="col-md-6">
//                                     <p><strong>Numer VAT:</strong> <span id="verification-vat-number"></span></p>
//                                 </div>
//                             </div>

//                             <div class="row mb-3">
//                                 <div class="col-md-6">
//                                     <p><strong>Data ostatniej weryfikacji:</strong> <span id="verification-date"></span></p>
//                                 </div>
//                                 <div class="col-md-6">
//                                     <p><strong>ID ostatniej weryfikacji:</strong> <span id="verification-id"></span></p>
//                                 </div>
//                             </div>

//                             <button type="button" class="btn btn-primary" id="verifyVATAgainBtn">
//                                 <i class="fas fa-sync-alt me-2"></i> Weryfikuj ponownie
//                             </button>
//                         </div>

//                         <div id="verification-history-section" class="mt-4 pt-4 border-top">
//                             <h5 class="mb-3">Historia weryfikacji</h5>
//                             <div class="table-responsive">
//                                 <table id="verification-history-table" class="table table-sm">
//                                     <thead>
//                                         <tr>
//                                             <th>Data</th>
//                                             <th>ID weryfikacji</th>
//                                             <th>Status</th>
//                                         </tr>
//                                     </thead>
//                                     <tbody>
//                                         <!-- Historia weryfikacji będzie dodawana dynamicznie -->
//                                     </tbody>
//                                 </table>
//                             </div>
//                         </div>
//                     </div>
//                 </div>
//             </div>
//         `);
//     },

//     /**
//      * Fill verification tab with data
//      * @param {Object} data Partner data
//      */
//     fillVerificationTab: function (data) {
//         // Fill VAT number with proper formatting - fix undefined issue
//         if (data.country && data.vat_number) {
//             $('#verification-vat-number').text(`${data.country}${data.vat_number}`);
//         } else {
//             $('#verification-vat-number').html('<span class="text-muted">Brak danych</span>');
//         }

//         // Fill verification status
//         if (data.is_verified) {
//             $('#verification-status').html('<span class="badge bg-success">Aktywny</span>');
//         } else {
//             $('#verification-status').html('<span class="badge bg-warning">Nieaktywny</span>');
//         }

//         // Fill verification date
//         if (data.verification_date) {
//             const date = new Date(data.verification_date);
//             $('#verification-date').text(date.toLocaleString());
//         } else {
//             $('#verification-date').html('<span class="text-muted">Brak danych</span>');
//         }

//         // Fill verification ID
//         if (data.verification_id) {
//             $('#verification-id').html(`<code>${data.verification_id}</code>`);
//         } else {
//             $('#verification-id').html('<span class="text-muted">Brak danych</span>');
//         }

//         // Add verification history if available
//         if (data.verification_history && data.verification_history.length > 0) {
//             $('#verification-history-table tbody').empty();

//             data.verification_history.forEach(function (entry) {
//                 const date = new Date(entry.verification_date);
//                 const formattedDate = date.toLocaleString();
//                 const status = entry.is_verified ?
//                     '<span class="badge bg-success">Aktywny</span>' :
//                     '<span class="badge bg-warning">Nieaktywny</span>';

//                 const historyEntry = `
//                 <tr>
//                     <td>${formattedDate}</td>
//                     <td>${entry.verification_id || '-'}</td>
//                     <td>${status}</td>
//                 </tr>
//             `;

//                 $('#verification-history-table tbody').append(historyEntry);
//             });

//             // Show history section
//             $('#verification-history-section').removeClass('d-none');
//         } else {
//             // Add a "no history" message instead of hiding
//             $('#verification-history-table tbody').html(`
//                 <tr>
//                     <td colspan="3" class="text-center text-muted">Brak historii weryfikacji</td>
//                 </tr>
//             `);
//         }
//     },

//     /**
//      * Initialize verify again button
//      */
//     // initVerifyAgainButton: function () {
//     //     $(document).on('click', '#verifyVATAgainBtn', function () {
//     //         const partnerId = $('#partner_id').val();
//     //         const country = $('#id_country_hidden').val();
//     //         const vatNumber = $('#id_vat_number_hidden').val();

//     //         // Show spinner
//     //         const button = $(this);
//     //         const originalText = button.html();
//     //         button.html('<span class="spinner-border spinner-border-sm me-2"></span>Weryfikacja...');
//     //         button.prop('disabled', true);

//     //         // Call VAT verification API
//     //         $.ajax({
//     //             url: "/partner/api/verify-vat/",
//     //             type: 'GET',
//     //             data: {
//     //                 country: country,
//     //                 vat_number: vatNumber
//     //             },
//     //             success: function (response) {
//     //                 if (response.success) {
//     //                     // Update the Partner in the database
//     //                     $.ajax({
//     //                         url: `/partner/api/update-verification/${partnerId}/`,
//     //                         type: 'POST',
//     //                         data: {
//     //                             csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
//     //                             is_verified: true,
//     //                             verification_id: response.data.verification_id || ''
//     //                         },
//     //                         success: function () {
//     //                             // Update verification tab data
//     //                             const newData = {
//     //                                 country: country,
//     //                                 vat_number: vatNumber,
//     //                                 is_verified: true,
//     //                                 verification_date: new Date().toISOString(),
//     //                                 verification_id: response.data.verification_id || ''
//     //                             };

//     //                             // Update the status display
//     //                             VATVerificationStatus.fillVerificationTab(newData);

//     //                             // Add to verification history
//     //                             VATVerificationStatus.addVerificationHistoryEntry(newData);

//     //                             // Show success message
//     //                             PartnerUtils.showModalMessage('Weryfikacja zakończona pomyślnie!', 'success');

//     //                             // Reset button
//     //                             button.html(originalText);
//     //                             button.prop('disabled', false);
//     //                         },
//     //                         error: function () {
//     //                             PartnerUtils.showModalMessage('Wystąpił błąd podczas aktualizacji statusu weryfikacji.', 'danger');
//     //                             button.html(originalText);
//     //                             button.prop('disabled', false);
//     //                         }
//     //                     });
//     //                 } else {
//     //                     // Show error
//     //                     PartnerUtils.showModalMessage(response.message || 'Weryfikacja nie powiodła się.', 'danger');
//     //                     button.html(originalText);
//     //                     button.prop('disabled', false);
//     //                 }
//     //             },
//     //             error: function () {
//     //                 PartnerUtils.showModalMessage('Wystąpił błąd podczas weryfikacji VAT.', 'danger');
//     //                 button.html(originalText);
//     //                 button.prop('disabled', false);
//     //             }
//     //         });
//     //     });
//     // },

//     // /**
//     //  * Add verification history entry
//     //  * @param {Object} data Verification data
//     //  */

//     initVerifyAgainButton: function () {
//         $(document).on('click', '#verifyVATAgainBtn', function () {
//             const partnerId = $('#partner_id').val();
//             const country = $('#id_country_hidden').val();
//             const vatNumber = $('#id_vat_number_hidden').val();

//             // Zapisz istniejącą historię
//             const existingHistory = [];
//             $('#verification-history-table tbody tr').each(function () {
//                 const row = {
//                     date: $(this).find('td:eq(0)').text(),
//                     id: $(this).find('td:eq(1)').text(),
//                     status: $(this).find('td:eq(2)').html()
//                 };
//                 existingHistory.push(row);
//             });

//             // Show spinner
//             const button = $(this);
//             const originalText = button.html();
//             button.html('<span class="spinner-border spinner-border-sm me-2"></span>Weryfikacja...');
//             button.prop('disabled', true);

//             // Call VAT verification API
//             $.ajax({
//                 url: "/partner/api/verify-vat/",
//                 type: 'GET',
//                 data: {
//                     country: country,
//                     vat_number: vatNumber
//                 },
//                 success: function (response) {
//                     if (response.success) {
//                         // Update the Partner in the database
//                         $.ajax({
//                             url: `/partner/api/update-verification/${partnerId}/`,
//                             type: 'POST',
//                             data: {
//                                 csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
//                                 is_verified: true,
//                                 verification_id: response.data.verification_id || ''
//                             },
//                             success: function (updateResponse) {
//                                 // Aktualizuj tylko dane statusu, nie całą kartę
//                                 const currentDate = new Date();

//                                 // Aktualizuj status
//                                 $('#verification-status').html('<span class="badge bg-success">Aktywny</span>');
//                                 $('#verification-date').text(currentDate.toLocaleString());
//                                 $('#verification-id').html(response.data.verification_id ?
//                                     `<code>${response.data.verification_id}</code>` :
//                                     '<span class="text-muted">Brak danych</span>');

//                                 // Dodaj nowy wpis historii na górze tabeli (bez kasowania istniejących)
//                                 const newEntry = `
//                                     <tr>
//                                         <td>${currentDate.toLocaleString()}</td>
//                                         <td>${response.data.verification_id || '-'}</td>
//                                         <td><span class="badge bg-success">Aktywny</span></td>
//                                     </tr>
//                                 `;

//                                 // Dodaj nowy wpis na początku tabeli
//                                 $('#verification-history-table tbody').prepend(newEntry);

//                                 // Pokaż sekcję historii (jeśli była ukryta)
//                                 $('#verification-history-section').removeClass('d-none');

//                                 // Pokaż komunikat sukcesu
//                                 PartnerUtils.showModalMessage('Weryfikacja zakończona pomyślnie!', 'success');

//                                 // Reset button
//                                 button.html(originalText);
//                                 button.prop('disabled', false);
//                             },
//                             error: function (xhr, status, error) {
//                                 console.error("Błąd aktualizacji weryfikacji:", error);
//                                 PartnerUtils.showModalMessage('Wystąpił błąd podczas aktualizacji statusu weryfikacji.', 'danger');
//                                 button.html(originalText);
//                                 button.prop('disabled', false);
//                             }
//                         });
//                     } else {
//                         // Show error
//                         PartnerUtils.showModalMessage(response.message || 'Weryfikacja nie powiodła się.', 'danger');
//                         button.html(originalText);
//                         button.prop('disabled', false);
//                     }
//                 },
//                 error: function (xhr, status, error) {
//                     console.error("Błąd weryfikacji VAT:", error);
//                     PartnerUtils.showModalMessage('Wystąpił błąd podczas weryfikacji VAT.', 'danger');
//                     button.html(originalText);
//                     button.prop('disabled', false);
//                 }
//             });
//         });
//     },


//     addVerificationHistoryEntry: function (data) {
//         const date = new Date(data.verification_date);
//         const formattedDate = date.toLocaleString();
//         const status = data.is_verified ?
//             '<span class="badge bg-success">Aktywny</span>' :
//             '<span class="badge bg-warning">Nieaktywny</span>';

//         const historyEntry = `
//             <tr>
//                 <td>${formattedDate}</td>
//                 <td>${data.verification_id || '-'}</td>
//                 <td>${status}</td>
//             </tr>
//         `;

//         // Add to history table
//         $('#verification-history-table tbody').prepend(historyEntry);

//         // Show history section if it was hidden
//         $('#verification-history-section').removeClass('d-none');
//     }
// };

/**
 * VAT Verification Status functionality
 */
const VATVerificationStatus = {
    // Ustawienia stronicowania
    paginationSettings: {
        itemsPerPage: 5, // Zmniejszyłem do 5 dla lepszego testowania
        currentPage: 1,
        totalPages: 1
    },

    // Tablica przechowująca pełną historię weryfikacji
    verificationHistory: [],

    /**
     * Initialize VAT verification status functionality
     */
    init: function () {
        this.initVerifyAgainButton();
        this.initPaginationListeners();
    },

    /**
     * Add verification tab to the modal
     */
    addVerificationTab: function () {
        // Check if verification tab already exists
        if ($('#verification-tab').length > 0) {
            return;
        }

        // Add tab button to the nav
        $('#partnerTabs').append(`
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="verification-tab" data-bs-toggle="tab" 
                       data-bs-target="#verification" type="button" role="tab" 
                       aria-controls="verification" aria-selected="false">
                    Weryfikacja VAT
                </button>
            </li>
        `);

        // Add tab content with new layout
        $('#partnerTabsContent').append(`
            <div class="tab-pane fade" id="verification" role="tabpanel" aria-labelledby="verification-tab">
                <div class="card border-0">
                    <div class="card-body">
                        <div class="mb-4">
                            <h5 class="mb-3">Aktualny status VAT</h5>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <p><strong>Status:</strong> <span id="verification-status"></span></p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>Numer VAT:</strong> <span id="verification-vat-number"></span></p>
                                </div>
                            </div>
                            
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <p><strong>Data ostatniej weryfikacji:</strong> <span id="verification-date"></span></p>
                                </div>
                                <div class="col-md-6">
                                    <p><strong>ID ostatniej weryfikacji:</strong> <span id="verification-id"></span></p>
                                </div>
                            </div>
                            
                            <button type="button" class="btn btn-primary" id="verifyVATAgainBtn">
                                <i class="fas fa-sync-alt me-2"></i> Weryfikuj ponownie
                            </button>
                        </div>
                        
                        <div id="verification-history-section" class="mt-4 pt-4 border-top">
                            <h5 class="mb-3">Historia weryfikacji</h5>
                            <div class="table-responsive">
                                <table id="verification-history-table" class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Data</th>
                                            <th>ID weryfikacji</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <!-- Historia weryfikacji będzie dodawana dynamicznie -->
                                    </tbody>
                                </table>
                            </div>
                            
                            <!-- Dodajemy nawigację stronicowania -->
                            <nav aria-label="Historia weryfikacji - stronicowanie" class="mt-3">
                                <ul class="pagination pagination-sm justify-content-center" id="verification-history-pagination">
                                    <!-- Przyciski stronicowania będą dodawane dynamicznie -->
                                </ul>
                            </nav>
                        </div>
                    </div>
                </div>
            </div>
        `);
    },

    /**
     * Fill verification tab with data
     * @param {Object} data Partner data
     */
    fillVerificationTab: function (data) {
        // Fill VAT number with proper formatting - fix undefined issue
        if (data.country_code && data.vat_number) {
            $('#verification-vat-number').text(`${data.country_code}${data.vat_number}`);
        } else if (data.country && data.vat_number) {
            $('#verification-vat-number').text(`${data.country}${data.vat_number}`);
        } else {
            $('#verification-vat-number').html('<span class="text-muted">Brak danych</span>');
        }

        // Fill verification status
        if (data.is_verified) {
            $('#verification-status').html('<span class="badge bg-success">Aktywny</span>');
        } else {
            $('#verification-status').html('<span class="badge bg-warning">Nieaktywny</span>');
        }

        // Fill verification date
        if (data.verification_date) {
            const date = new Date(data.verification_date);
            $('#verification-date').text(date.toLocaleString());
        } else {
            $('#verification-date').html('<span class="text-muted">Brak danych</span>');
        }

        // Fill verification ID
        if (data.verification_id) {
            $('#verification-id').html(`<code>${data.verification_id}</code>`);
        } else {
            $('#verification-id').html('<span class="text-muted">Brak danych</span>');
        }

        // Obsługa historii weryfikacji
        if (data.verification_history && data.verification_history.length > 0) {
            // Zapisz historię weryfikacji do zmiennej globalnej
            this.verificationHistory = data.verification_history;

            // Oblicz całkowitą liczbę stron
            this.paginationSettings.totalPages = Math.ceil(
                this.verificationHistory.length / this.paginationSettings.itemsPerPage
            );

            // Ustaw domyślnie pierwszą stronę
            this.paginationSettings.currentPage = 1;

            // Wyświetl pierwszą stronę historii
            this.displayHistoryPage(1);

            // Pokaż sekcję historii
            $('#verification-history-section').removeClass('d-none');
        } else {
            // Jeśli nie ma historii, wyczyść tabelę i dodaj komunikat
            $('#verification-history-table tbody').html(`
                <tr>
                    <td colspan="3" class="text-center text-muted">Brak historii weryfikacji</td>
                </tr>
            `);

            // Ukryj stronicowanie
            $('#verification-history-pagination').empty();
        }
    },

    /**
     * Display a specific page of history
     * @param {number} page Page number to display
     */
    displayHistoryPage: function (page) {
        // Sprawdź, czy mamy dane historii
        if (!this.verificationHistory || this.verificationHistory.length === 0) {
            return;
        }

        // Zabezpieczenie przed nieprawidłowym numerem strony
        if (page < 1) page = 1;
        if (page > this.paginationSettings.totalPages) page = this.paginationSettings.totalPages;

        // Zaktualizuj bieżącą stronę
        this.paginationSettings.currentPage = page;

        // Oblicz indeksy dla tej strony
        const startIndex = (page - 1) * this.paginationSettings.itemsPerPage;
        const endIndex = Math.min(startIndex + this.paginationSettings.itemsPerPage, this.verificationHistory.length);

        // Wyczyść tabelę historii
        $('#verification-history-table tbody').empty();

        // Dodaj wpisy dla tej strony
        for (let i = startIndex; i < endIndex; i++) {
            const entry = this.verificationHistory[i];
            const date = new Date(entry.verification_date);
            const formattedDate = date.toLocaleString();
            const status = entry.is_verified ?
                '<span class="badge bg-success">Aktywny</span>' :
                '<span class="badge bg-warning">Nieaktywny</span>';

            const historyEntry = `
                <tr>
                    <td>${formattedDate}</td>
                    <td>${entry.verification_id || '-'}</td>
                    <td>${status}</td>
                </tr>
            `;

            $('#verification-history-table tbody').append(historyEntry);
        }

        // Zaktualizuj przyciski stronicowania
        this.updatePagination();
    },

    /**
     * Update pagination controls
     */
    updatePagination: function () {
        const pagination = $('#verification-history-pagination');
        pagination.empty();

        // Jeśli jest tylko jedna strona, nie pokazuj kontrolek stronicowania
        if (this.paginationSettings.totalPages <= 1) {
            return;
        }

        // Dodaj przycisk "Poprzednia"
        pagination.append(`
            <li class="page-item ${this.paginationSettings.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.paginationSettings.currentPage - 1}">
                    &laquo;
                </a>
            </li>
        `);

        // Dodaj numery stron
        for (let i = 1; i <= this.paginationSettings.totalPages; i++) {
            pagination.append(`
                <li class="page-item ${this.paginationSettings.currentPage === i ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }

        // Dodaj przycisk "Następna"
        pagination.append(`
            <li class="page-item ${this.paginationSettings.currentPage === this.paginationSettings.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.paginationSettings.currentPage + 1}">
                    &raquo;
                </a>
            </li>
        `);
    },

    /**
     * Initialize pagination event listeners
     */
    initPaginationListeners: function () {
        // Używamy delegacji zdarzeń, aby obsłużyć przyciski stronicowania
        $(document).on('click', '#verification-history-pagination .page-link', function (e) {
            e.preventDefault();

            const page = parseInt($(this).data('page'));
            if (!isNaN(page)) {
                VATVerificationStatus.displayHistoryPage(page);
            }
        });
    },

    /**
     * Initialize verify again button
     */
    initVerifyAgainButton: function () {
        $(document).on('click', '#verifyVATAgainBtn', function () {
            const partnerId = $('#partner_id').val();
            const country = $('#id_country_hidden').val();
            const vatNumber = $('#id_vat_number_hidden').val();

            // Show spinner
            const button = $(this);
            const originalText = button.html();
            button.html('<span class="spinner-border spinner-border-sm me-2"></span>Weryfikacja...');
            button.prop('disabled', true);

            // Call VAT verification API
            $.ajax({
                url: "/partner/api/verify-vat/",
                type: 'GET',
                data: {
                    country: country,
                    vat_number: vatNumber
                },
                success: function (response) {
                    if (response.success) {
                        // Update the Partner in the database
                        $.ajax({
                            url: `/partner/api/update-verification/${partnerId}/`,
                            type: 'POST',
                            data: {
                                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
                                is_verified: true,
                                verification_id: response.data.verification_id || ''
                            },
                            success: function (updateResponse) {
                                // Aktualizuj tylko dane statusu, nie całą kartę
                                const currentDate = new Date();

                                // Aktualizuj status
                                $('#verification-status').html('<span class="badge bg-success">Aktywny</span>');
                                $('#verification-date').text(currentDate.toLocaleString());
                                $('#verification-id').html(response.data.verification_id ?
                                    `<code>${response.data.verification_id}</code>` :
                                    '<span class="text-muted">Brak danych</span>');

                                // Po weryfikacji pobierz partnera na nowo, aby uzyskać aktualną historię
                                $.ajax({
                                    url: `/partner/api/get/${partnerId}/`,
                                    type: 'GET',
                                    success: function (partnerData) {
                                        if (partnerData.success) {
                                            // Aktualizuj historię weryfikacji
                                            if (partnerData.data.verification_history) {
                                                VATVerificationStatus.verificationHistory = partnerData.data.verification_history;

                                                // Aktualizuj liczbę stron
                                                VATVerificationStatus.paginationSettings.totalPages = Math.ceil(
                                                    VATVerificationStatus.verificationHistory.length /
                                                    VATVerificationStatus.paginationSettings.itemsPerPage
                                                );

                                                // Wyświetl pierwszą stronę z nową historią
                                                VATVerificationStatus.paginationSettings.currentPage = 1;
                                                VATVerificationStatus.displayHistoryPage(1);
                                            }
                                        } else {
                                            // Jeśli nie udało się pobrać partnera, dodaj nowy wpis do istniejącej historii
                                            VATVerificationStatus.addNewHistoryEntry(currentDate, response.data.verification_id, true);
                                        }
                                    },
                                    error: function () {
                                        // W przypadku błędu, dodaj nowy wpis do istniejącej historii
                                        VATVerificationStatus.addNewHistoryEntry(currentDate, response.data.verification_id, true);
                                    }
                                });

                                // Pokaż komunikat sukcesu
                                PartnerUtils.showModalMessage('Weryfikacja zakończona pomyślnie!', 'success');

                                // Reset button
                                button.html(originalText);
                                button.prop('disabled', false);
                            },
                            error: function (xhr, status, error) {
                                console.error("Błąd aktualizacji weryfikacji:", error);
                                PartnerUtils.showModalMessage('Wystąpił błąd podczas aktualizacji statusu weryfikacji.', 'danger');
                                button.html(originalText);
                                button.prop('disabled', false);
                            }
                        });
                    } else {
                        // Show error
                        PartnerUtils.showModalMessage(response.message || 'Weryfikacja nie powiodła się.', 'danger');
                        button.html(originalText);
                        button.prop('disabled', false);
                    }
                },
                error: function (xhr, status, error) {
                    console.error("Błąd weryfikacji VAT:", error);
                    PartnerUtils.showModalMessage('Wystąpił błąd podczas weryfikacji VAT.', 'danger');
                    button.html(originalText);
                    button.prop('disabled', false);
                }
            });
        });
    },

    /**
     * Add new history entry to the existing history
     * @param {Date} date Date of verification
     * @param {string} verificationId Verification ID
     * @param {boolean} isVerified Verification status
     */
    addNewHistoryEntry: function (date, verificationId, isVerified) {
        // Dodaj nowy wpis do historii
        if (!this.verificationHistory) {
            this.verificationHistory = [];
        }

        // Dodaj nowy wpis na początku tablicy
        this.verificationHistory.unshift({
            verification_date: date.toISOString(),
            verification_id: verificationId || '',
            is_verified: isVerified
        });

        // Aktualizuj liczbę stron
        this.paginationSettings.totalPages = Math.ceil(
            this.verificationHistory.length / this.paginationSettings.itemsPerPage
        );

        // Wyświetl pierwszą stronę
        this.paginationSettings.currentPage = 1;
        this.displayHistoryPage(1);
    },

    /**
     * Add verification history entry (zachowana dla kompatybilności)
     * @param {Object} data Verification data
     */
    addVerificationHistoryEntry: function (data) {
        const date = new Date(data.verification_date);

        // Używamy nowej metody do dodania wpisu
        this.addNewHistoryEntry(date, data.verification_id, data.is_verified);

        // Show history section if it was hidden
        $('#verification-history-section').removeClass('d-none');
    }
};