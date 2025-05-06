/**
 * Partner edit functionality module
 */
const PartnerEdit = {
    /**
     * Initialize edit functionality
     */
    init: function () {
        this.initEditButtons();
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

            // Hide step 1 and loader, show step 2
            $('#step1').addClass('d-none');
            $('#verification-loader').addClass('d-none');
            $('#step2').removeClass('d-none');

            // Change save button text
            $('#savePartnerBtn').text('Zapisz zmiany');
            $('#savePartnerBtn').prop('disabled', false);

            // Clear form fields, especially emails
            $('#id_email_contacts').val(null).trigger('change');

            // Get partner data
            PartnerAPI.getPartner(partnerId,
                // Success callback
                function (data) {
                    // Fill form with partner data
                    PartnerForm.fillFormWithPartnerData(data);

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
    }
};