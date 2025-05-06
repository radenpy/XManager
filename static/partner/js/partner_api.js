/**
 * API communication module for partner operations
 */
const PartnerAPI = {
    /**
     * Get partner data by ID
     * @param {number} partnerId - The ID of the partner to get
     * @param {function} successCallback - Callback function on success
     * @param {function} errorCallback - Callback function on error
     */
    getPartner: function (partnerId, successCallback, errorCallback) {
        $.ajax({
            url: `/partner/api/get/${partnerId}/`,
            type: 'GET',
            success: function (response) {
                if (response.success) {
                    successCallback(response.data);
                } else {
                    errorCallback(response.message || 'Nie udało się pobrać danych partnera');
                }
            },
            error: function (xhr, status, error) {
                errorCallback('Wystąpił błąd podczas pobierania danych: ' + error);
            }
        });
    },

    /**
     * Create a new partner
     * @param {FormData} formData - Form data for the new partner
     * @param {function} successCallback - Callback function on success
     * @param {function} errorCallback - Callback function on error
     */
    createPartner: function (formData, successCallback, errorCallback) {
        $.ajax({
            url: "/partner/api/create/",
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.success) {
                    successCallback(response.message || 'Partner został dodany pomyślnie');
                } else {
                    errorCallback(response.message || 'Nie udało się dodać partnera');
                }
            },
            error: function (xhr, status, error) {
                errorCallback('Wystąpił błąd podczas zapisywania: ' + error);
            }
        });
    },

    /**
     * Update an existing partner
     * @param {number} partnerId - The ID of the partner to update
     * @param {FormData} formData - Form data with updated partner information
     * @param {function} successCallback - Callback function on success
     * @param {function} errorCallback - Callback function on error
     */
    updatePartner: function (partnerId, formData, successCallback, errorCallback) {
        $.ajax({
            url: `/partner/api/update/${partnerId}/`,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.success) {
                    successCallback(response.message || 'Partner został zaktualizowany pomyślnie');
                } else {
                    errorCallback(response.message || 'Nie udało się zaktualizować partnera');
                }
            },
            error: function (xhr, status, error) {
                errorCallback('Wystąpił błąd podczas zapisywania: ' + error);
            }
        });
    },

    /**
     * Verify a VAT number
     * @param {string} country - Country code
     * @param {string} vatNumber - VAT number to verify
     * @param {function} successCallback - Callback function on success
     * @param {function} errorCallback - Callback function on error
     */
    verifyVAT: function (country, vatNumber, successCallback, errorCallback) {
        $.ajax({
            url: "/partner/api/verify-vat/",
            type: 'GET',
            data: {
                country: country,
                vat_number: vatNumber
            },
            success: function (response) {
                if (response.success) {
                    successCallback(response.data);
                } else {
                    errorCallback(response.message || 'Nie udało się zweryfikować numeru VAT');
                }
            },
            error: function (xhr, status, error) {
                errorCallback('Wystąpił błąd podczas weryfikacji: ' + error);
            }
        });
    },

    /**
     * Delete a partner
     * @param {number} partnerId - The ID of the partner to delete
     * @param {function} successCallback - Callback function on success
     * @param {function} errorCallback - Callback function on error
     */
    deletePartner: function (partnerId, successCallback, errorCallback) {
        $.ajax({
            url: `/partner/api/delete/${partnerId}/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function (response) {
                if (response.success) {
                    successCallback(response.message || 'Partner został usunięty');
                } else {
                    errorCallback(response.message || 'Nie udało się usunąć partnera');
                }
            },
            error: function (xhr, status, error) {
                errorCallback('Wystąpił błąd podczas usuwania: ' + error);
            }
        });
    }
};