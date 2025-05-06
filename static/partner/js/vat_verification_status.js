/**
 * VAT Verification Status functionality
 */
const VATVerificationStatus = {
    /**
     * Initialize VAT verification status functionality
     */
    init: function () {
        this.initVerifyAgainButton();
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
        if (data.country && data.vat_number) {
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

        // Add verification history if available
        if (data.verification_history && data.verification_history.length > 0) {
            $('#verification-history-table tbody').empty();

            data.verification_history.forEach(function (entry) {
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
            });

            // Show history section
            $('#verification-history-section').removeClass('d-none');
        } else {
            // Add a "no history" message instead of hiding
            $('#verification-history-table tbody').html(`
                <tr>
                    <td colspan="3" class="text-center text-muted">Brak historii weryfikacji</td>
                </tr>
            `);
        }
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
                            success: function () {
                                // Update verification tab data
                                const newData = {
                                    country: country,
                                    vat_number: vatNumber,
                                    is_verified: true,
                                    verification_date: new Date().toISOString(),
                                    verification_id: response.data.verification_id || ''
                                };

                                // Update the status display
                                VATVerificationStatus.fillVerificationTab(newData);

                                // Add to verification history
                                VATVerificationStatus.addVerificationHistoryEntry(newData);

                                // Show success message
                                PartnerUtils.showModalMessage('Weryfikacja zakończona pomyślnie!', 'success');

                                // Reset button
                                button.html(originalText);
                                button.prop('disabled', false);
                            },
                            error: function () {
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
                error: function () {
                    PartnerUtils.showModalMessage('Wystąpił błąd podczas weryfikacji VAT.', 'danger');
                    button.html(originalText);
                    button.prop('disabled', false);
                }
            });
        });
    },

    /**
     * Add verification history entry
     * @param {Object} data Verification data
     */
    addVerificationHistoryEntry: function (data) {
        const date = new Date(data.verification_date);
        const formattedDate = date.toLocaleString();
        const status = data.is_verified ?
            '<span class="badge bg-success">Aktywny</span>' :
            '<span class="badge bg-warning">Nieaktywny</span>';

        const historyEntry = `
            <tr>
                <td>${formattedDate}</td>
                <td>${data.verification_id || '-'}</td>
                <td>${status}</td>
            </tr>
        `;

        // Add to history table
        $('#verification-history-table tbody').prepend(historyEntry);

        // Show history section if it was hidden
        $('#verification-history-section').removeClass('d-none');
    }
};