/**
 * Utility functions for partner management
 */
const PartnerUtils = {
    /**
     * Display a message in the modal
     * @param {string} message - Message text
     * @param {string} type - Message type (success, danger, warning, info)
     */
    showModalMessage: function (message, type) {
        // Remove existing messages
        $('.modal-message').remove();

        // Create message element
        const messageElement = $(`
            <div class="alert alert-${type} modal-message mb-3">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `);

        // Add message to modal
        $('#partnerForm').prepend(messageElement);
    },

    /**
     * Display a message in the main container
     * @param {string} message - Message text
     * @param {string} type - Message type (success, danger, warning, info)
     */
    showMessage: function (message, type) {
        const alertBox = $(`<div class="alert alert-${type} alert-dismissible fade show" role="alert">
                            ${message}
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            </div>`);

        $('.messages-container').append(alertBox);

        // Auto-hide after 5 seconds
        setTimeout(function () {
            alertBox.alert('close');
        }, 5000);
    },

    /**
     * Format a country option for Select2
     * @param {Object} country - Country object
     * @return {jQuery} Formatted option
     */
    formatCountryOption: function (country) {
        if (!country.id) {
            return country.text;
        }

        const flag = country.element ? $(country.element).data('flag') : '';

        return $(`
            <div>
                <span class="flag-icon flag-icon-${flag} me-2"></span>
                ${country.text}
            </div>
        `);
    },

    /**
     * Format a selected country for Select2
     * @param {Object} country - Country object
     * @return {jQuery} Formatted selection
     */
    formatCountrySelection: function (country) {
        if (!country.id) {
            return country.text;
        }

        const flag = country.element ? $(country.element).data('flag') : '';

        return $(`
            <div>
                <span class="flag-icon flag-icon-${flag} me-2"></span>
                ${country.text}
            </div>
        `);
    }
};