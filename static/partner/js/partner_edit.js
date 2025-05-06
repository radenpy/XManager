/**
 * Partner edit functionality module
 */
const PartnerEdit = {
    /**
     * Initialize edit functionality
     */
    init: function () {
        this.initEditButtons();

        // Initialize tabs
        this.initTabs();

        // Initialize VAT verification functionality
        VATVerificationStatus.init();
    },

    /**
     * Initialize edit buttons
     */
    initEditButtons: function () {
        $('.edit-partner').on('click', function (e) {
            e.preventDefault();
            const partnerId = $(this).data('partner-id');

            // Change modal title
            $('#addPartnerModalLabel').text('Edytuj partnera');

            // Hide VAT verification success message
            $('#step2 .alert-success').addClass('d-none');

            // Hide step 1, show step 2
            $('#step1').addClass('d-none');
            $('#verification-loader').addClass('d-none');
            $('#step2').removeClass('d-none');

            // Add tabs if they don't exist
            PartnerEdit.addTabsToModal();

            // Add verification tab
            VATVerificationStatus.addVerificationTab();

            // Change save button text
            $('#savePartnerBtn').text('Zapisz zmiany');
            $('#savePartnerBtn').prop('disabled', false);

            // Clear form fields
            $('#id_email_contacts').val(null).trigger('change');

            // Get partner data
            PartnerAPI.getPartner(partnerId,
                // Success callback
                function (data) {
                    // Fill form with partner data
                    PartnerForm.fillFormWithPartnerData(data);

                    // Fill verification tab with data
                    VATVerificationStatus.fillVerificationTab(data);

                    // Add hidden field with partner ID
                    if ($('#partner_id').length === 0) {
                        $('<input>').attr({
                            type: 'hidden',
                            name: 'partner_id',
                            id: 'partner_id',
                            value: partnerId
                        }).appendTo('#partnerForm');
                    } else {
                        $('#partner_id').val(partnerId);
                    }

                    // Show modal
                    $('#addPartnerModal').modal('show');
                },
                // Error callback
                function (errorMessage) {
                    PartnerUtils.showMessage(errorMessage, 'danger');
                }
            );
        });

        // Add event listener for email unselect
        $('#id_email_contacts').on('select2:unselect', function (e) {
            console.log('Email unselected:', e.params.data.text);
        });
    },

    /**
     * Initialize tabs
     */
    initTabs: function () {
        // Handle modal show event to ensure proper tab activation
        $('#addPartnerModal').on('shown.bs.modal', function () {
            // Ensure the first tab is active
            $('#details-tab').tab('show');
        });

        // Handle tab switching
        $(document).on('click', '.nav-link[data-bs-toggle="tab"]', function (e) {
            e.preventDefault();
            $(this).tab('show');

            // If switching to emails tab, make sure Select2 is properly initialized
            if ($(this).attr('id') === 'emails-tab') {
                setTimeout(function () {
                    PartnerForm.initializeEmailSelect();
                }, 100);
            }
        });
    },

    /**
     * Add tabs to modal
     */
    addTabsToModal: function () {
        // Check if tabs already exist
        if ($('#partnerTabs').length > 0) {
            return;
        }

        // Create tabs structure
        const tabsHtml = `
            <ul class="nav nav-tabs mb-4" id="partnerTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="details-tab" data-bs-toggle="tab" 
                           data-bs-target="#details" type="button" role="tab" 
                           aria-controls="details" aria-selected="true">
                        Dane partnera
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="emails-tab" data-bs-toggle="tab" 
                           data-bs-target="#emails" type="button" role="tab" 
                           aria-controls="emails" aria-selected="false">
                        Powiązane emaile
                    </button>
                </li>
            </ul>
            
            <div class="tab-content" id="partnerTabsContent">
                <div class="tab-pane fade show active" id="details" role="tabpanel" 
                     aria-labelledby="details-tab">
                    <!-- Will be filled with current form content -->
                </div>
                <div class="tab-pane fade" id="emails" role="tabpanel" 
                     aria-labelledby="emails-tab">
                    <!-- Email contacts tab content -->
                    <h3 class="mb-4">Powiązane emaile partnera</h3>
                    <div class="mb-3">
                        <select id="id_email_contacts" name="email_contacts" class="form-control select2-emails" multiple>
                            <!-- Wybrane emaile pojawią się tutaj -->
                        </select>
                        <div class="mt-2 small text-muted">
                            Wybierz istniejące adresy email lub dodaj nowe. Możesz usunąć adres klikając na X obok niego.
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Get the current content of step2
        const formContent = $('#step2').html();

        // Create a temporary container to manipulate the content
        const $tempContainer = $('<div>').html(formContent);

        // Remove the email section from the original content
        $tempContainer.find('h6:contains("Powiązane adresy email"), div:has(select#id_email_contacts), select#id_email_contacts, .select2-container').remove();

        // Get the cleaned content
        const cleanedContent = $tempContainer.html();

        // Replace step2 content with tabs
        $('#step2').html(tabsHtml);

        // Put the cleaned content into the details tab
        $('#details').html(cleanedContent);

        // Inicjalizuj Select2 po dodaniu zakładek
        setTimeout(function () {
            PartnerForm.initializeEmailSelect();
        }, 100);
    }
};