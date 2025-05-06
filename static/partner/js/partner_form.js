/**
 * Partner form handling module
 */
const PartnerForm = {
    /**
     * Initialize the partner form
     */
    init: function () {
        this.initSelects();
        this.initVerifyButton();
        this.initSaveButton();
        this.initModalEvents();
        this.initDeleteButtons();
    },

    /**
     * Initialize Select2 components
     */
    initSelects: function () {
        // Initialize Select2 for countries
        $('.select2-countries').select2({
            dropdownParent: $('#addPartnerModal'),
            templateResult: PartnerUtils.formatCountryOption,
            templateSelection: PartnerUtils.formatCountrySelection,
            placeholder: "Wybierz kraj",
            allowClear: true,
            language: {
                inputTooShort: function () {
                    return "Wpisz co najmniej 1 znak...";
                },
                noResults: function () {
                    return "Brak wyników";
                },
                searching: function () {
                    return "Wyszukiwanie...";
                }
            }
        });

        // Initialize Select2 for emails
        $('.select2-emails').select2({
            dropdownParent: $('#addPartnerModal'),
            tags: true,
            placeholder: 'Wybierz lub dodaj adresy email',
            ajax: {
                url: "/partner/api/subscribers/lookup/",
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        search: params.term,
                        page: params.page || 1
                    };
                },
                processResults: function (data) {
                    return {
                        results: data.results.map(function (item) {
                            return {
                                id: item.id,
                                text: item.email,
                                full_name: (item.first_name && item.last_name) ? `${item.first_name} ${item.last_name}` : null
                            };
                        }),
                        pagination: {
                            more: data.has_more
                        }
                    };
                },
                cache: true
            },
            maximumSelectionLength: 10
        });
    },

    /**
     * Initialize VAT verification button
     */
    initVerifyButton: function () {
        $('#verifyVATBtn').on('click', function () {
            const country = $('#id_country').val();
            const vatNumber = $('#id_vat_number').val();

            if (!country || !vatNumber) {
                PartnerUtils.showModalMessage('Wybierz kraj i wprowadź numer VAT', 'danger');
                return;
            }

            // Show loader
            $('#step1').addClass('d-none');
            $('#verification-loader').removeClass('d-none');

            // Call VAT verification API
            PartnerAPI.verifyVAT(country, vatNumber,
                // Success callback
                function (data) {
                    // Hide loader
                    $('#verification-loader').addClass('d-none');

                    // Fill form with verification data
                    PartnerForm.fillFormWithVerificationData(data);

                    // Show step 2
                    $('#step2').removeClass('d-none');

                    // Enable save button
                    $('#savePartnerBtn').prop('disabled', false);
                },
                // Error callback
                function (errorMessage) {
                    // Hide loader and show error
                    $('#verification-loader').addClass('d-none');
                    $('#step1').removeClass('d-none');
                    PartnerUtils.showModalMessage(errorMessage, 'danger');
                }
            );
        });
    },

    /**
     * Initialize save button
     */
    initSaveButton: function () {
        $('#savePartnerBtn').on('click', function () {
            // Check if we're in edit mode
            const isEditMode = $('#partner_id').length > 0;
            const partnerId = isEditMode ? $('#partner_id').val() : null;

            // Collect form data
            const formData = new FormData(document.getElementById('partnerForm'));

            // Add email addresses
            const emails = $('#id_email_contacts').val();
            if (emails && emails.length > 0) {
                emails.forEach(function (email) {
                    formData.append('email_contacts', email);
                });
            }

            // Debug: Log what's being sent
            console.log("Email contacts being sent:", $('#id_email_contacts').val());
            formData.forEach((value, key) => {
                console.log(key, value);
            });

            if (isEditMode) {
                // Update existing partner
                PartnerAPI.updatePartner(partnerId, formData,
                    // Success callback
                    function (message) {
                        // Close modal
                        $('#addPartnerModal').modal('hide');

                        // Show success message
                        PartnerUtils.showMessage(message, 'success');

                        // Refresh page after 1 second
                        setTimeout(function () {
                            window.location.reload();
                        }, 1000);
                    },
                    // Error callback
                    function (errorMessage) {
                        PartnerUtils.showModalMessage(errorMessage, 'danger');
                    }
                );
            } else {
                // Create new partner
                PartnerAPI.createPartner(formData,
                    // Success callback
                    function (message) {
                        // Close modal
                        $('#addPartnerModal').modal('hide');

                        // Show success message
                        PartnerUtils.showMessage(message, 'success');

                        // Refresh page after 1 second
                        setTimeout(function () {
                            window.location.reload();
                        }, 1000);
                    },
                    // Error callback
                    function (errorMessage) {
                        PartnerUtils.showModalMessage(errorMessage, 'danger');
                    }
                );
            }
        });
    },

    /**
     * Initialize modal events
     */
    initModalEvents: function () {
        $('#addPartnerModal').on('hidden.bs.modal', function () {
            // Reset form
            $('#partnerForm')[0].reset();

            // Restore original modal title
            $('#addPartnerModalLabel').text('Dodaj partnera');

            // Restore original save button text
            $('#savePartnerBtn').text('Zapisz partnera');

            // Remove partner ID field
            $('#partner_id').remove();

            // Show verification success message (default)
            $('#step2 .alert-success').removeClass('d-none');

            // Hide step 2, show step 1
            $('#step1').removeClass('d-none');
            $('#step2').addClass('d-none');
            $('#verification-loader').addClass('d-none');

            // Reset Select2 components
            $('#id_country').val(null).trigger('change');
            $('#id_email_contacts').val(null).trigger('change');

            // Disable save button
            $('#savePartnerBtn').prop('disabled', true);

            // Remove messages
            $('.modal-message').remove();
        });
    },

    /**
     * Initialize delete buttons
     */
    initDeleteButtons: function () {
        $('.delete-partner').on('click', function () {
            const partnerId = $(this).data('partner-id');

            // Set delete form action
            $('#deletePartnerForm').attr('action', `/partner/delete/${partnerId}/`);

            // Show confirmation modal
            $('#deletePartnerModal').modal('show');
        });
    },

    /**
     * Fill form with verification data
     * @param {Object} data - Verification data
     */
    fillFormWithVerificationData: function (data) {
        // Fill form fields
        $('#id_name').val(data.name || '');
        $('#id_city').val(data.city || '');
        $('#id_street_name').val(data.street_name || '');
        $('#id_building_number').val(data.building_number || '');
        $('#id_postal_code').val(data.postal_code || '');

        // Save verification ID
        $('#id_verification_id').val(data.verification_id || '');

        // Fill VAT number and country fields
        const country = $('#id_country').val();
        const vatNumber = $('#id_vat_number').val();

        // Get country name from selected option
        const countryName = $('#id_country option:selected').text();

        $('#id_vat_number_display').val(vatNumber);
        $('#id_vat_number_hidden').val(vatNumber);
        $('#id_country_display').val(countryName);
        $('#id_country_hidden').val(country);

        // Display country prefix
        $('.country-prefix').text(country);
    },

    /**
     * Fill form with partner data (for editing)
     * @param {Object} data - Partner data
     */
    fillFormWithPartnerData: function (data) {
        // Fill form fields
        $('#id_name').val(data.name || '');
        $('#id_city').val(data.city || '');
        $('#id_street_name').val(data.street_name || '');
        $('#id_building_number').val(data.building_number || '');
        $('#id_apartment_number').val(data.apartment_number || '');
        $('#id_postal_code').val(data.postal_code || '');
        $('#id_phone_number').val(data.phone_number || '');
        $('#id_additional_info').val(data.additional_info || '');

        // Fill VAT number and country fields
        $('#id_vat_number_display').val(data.vat_number || '');
        $('#id_vat_number_hidden').val(data.vat_number || '');
        $('#id_country_display').val(data.country_name || '');
        $('#id_country_hidden').val(data.country_code || '');

        // Display country prefix
        $('.country-prefix').text(data.country_code || '');

        // Set associated email addresses
        if (data.emails && data.emails.length > 0) {
            const emailOptions = data.emails.map(email => {
                return new Option(email.email, email.id, true, true);
            });

            $('#id_email_contacts').empty().append(emailOptions).trigger('change');
        }
    }
};