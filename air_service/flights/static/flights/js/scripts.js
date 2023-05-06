function statusChangeCallback(response) {  // Called with the results from FB.getLoginStatus().
    console.log('statusChangeCallback');
    console.log(response);                   // The current login status of the person.
    if (response.status === 'connected') {   // Logged into your webpage and Facebook.
        testAPI();
    } else {                                 // Not logged into your webpage or we are unable to tell.
        document.getElementById('status').innerHTML = 'Please log ' +
            'into this webpage.';
    }
}


function checkLoginState() {               // Called when a person is finished with the Login Button.
    FB.getLoginStatus(function (response) {   // See the onlogin handler
        statusChangeCallback(response);
    });
}


window.fbAsyncInit = function () {
    FB.init({
        appId: '{app-id}',
        cookie: true,                     // Enable cookies to allow the server to access the session.
        xfbml: true,                     // Parse social plugins on this webpage.
        version: '{api-version}'           // Use this Graph API version for this call.
    });


    FB.getLoginStatus(function (response) {   // Called after the JS SDK has been initialized.
        statusChangeCallback(response);        // Returns the login status.
    });
};

function testAPI() {                      // Testing Graph API after login.  See statusChangeCallback() for when this call is made.
    console.log('Welcome!  Fetching your information.... ');
    FB.api('/me', function (response) {
        console.log('Successful login for: ' + response.name);
        document.getElementById('status').innerHTML =
            'Thanks for logging in, ' + response.name + '!';
    });
}

$(document).ready(function () {
    // console.log('Document is ready.');
    // console.log('Extra select element:', $('#id_extra'));

    // Обработчик событий для создания нового элемента выбора

    let selectedValues = [];

    function updateSelectOptions() {
        $('.extra-select').each(function () {
            const currentValue = $(this).val();
            const options = $('#id_extra option').clone();

            $(this).empty();

            options.each((index, option) => {
                if (option.value === currentValue || (selectedValues.indexOf(option.value) === -1 && option.value !== ' ')) {
                    $(this).append(option);
                }
            });
        });
    }

    function addNewSelect(event) {
        let selectedValue = $(this).val();
        let isNewSelect = !$(this).is('#id_extra');

        if (isNewSelect && selectedValue === ' ') {
            $(this).parent().remove();
        }

        if (selectedValue !== ' ') {
            selectedValues.push(selectedValue);
        } else {
            const index = selectedValues.indexOf($(this).attr('data-prev-value'));
            if (index > -1) {
                selectedValues.splice(index, 1);
            }
        }
        updateSelectOptions();

        if (!isNewSelect && selectedValue !== ' ' || isNewSelect && selectedValue !== ' ') {
            let newSelect = $('<select class="extra-select form-control custom-select"></select>');
            newSelect.html($('#id_extra').html());

            let formGroup = $('<div class="col-xxl-12"></div>');
            let label = $('<label class="mb-3">More Extra</label>');

            formGroup.append(label);
            formGroup.append(newSelect);
            $('#extra-select-container').append(formGroup);

            newSelect.on('change', addNewSelect);
        }

        updatePrice(); // Update the price when the select value changes
    }

    function addNewCheckbox(event) {
        const isChecked = $(this).prop('checked');
        const checkboxValue = $(this).val();

        if (isChecked) {
            selectedValues.push(checkboxValue);
        } else {
            const index = selectedValues.indexOf(checkboxValue);
            if (index > -1) {
                selectedValues.splice(index, 1);
            }
        }

        updateSelectOptions();

        updatePrice(); // Update the price when the checkbox state changes
    }

    $('#id_extra').on('change', addNewSelect);

    // ...

    const basePrice = parseInt($('#price-container-top').data('base-price'));
    const rowLetterSelect = $('#id_row_letter');
    const seatTypeSelect = $('#id_seat_type');
    const seatExtraSelect = $('#id_extra');

    function updatePrice() {
        let rowLetterFactor = parseInt(rowLetterSelect.find(':selected').data('price-factor')) || 0;
        let seatTypeFactor = parseInt(seatTypeSelect.find(':selected').data('price-factor')) || 0;

        let seatExtraFactor = parseInt(seatExtraSelect.find(':selected').data('price-factor')) || 0;
        $('.extra-select').each(function () {
            let extraFactor = parseInt($(this).find(':selected').data('price-factor')) || 0;
            seatExtraFactor += extraFactor;
        });

        // Добавьте этот код, чтобы учитывать галочки при обновлении цены
        $('.extra-checkbox:checked').each(function () {
            let extraFactor = parseInt($(this).data(`price-factor-${$(this).val()}`)) || 0;
            seatExtraFactor += extraFactor;
        });

        let newPrice = basePrice + rowLetterFactor + seatTypeFactor + seatExtraFactor;

        // Обновите оба контейнера с ценой
        $('#price-container-top').text(`Price: ${newPrice.toFixed(1)}$`);
        $('#price-container-bottom').text(`Price: ${newPrice.toFixed(1)}$`);

        // Вызовите функцию sendPriceToServer с обновленной ценой
        sendPriceToServer(newPrice.toFixed(1));
        // console.log(seatExtraSelect.val());
    }

    rowLetterSelect.on('change', updatePrice);
    seatTypeSelect.on('change', updatePrice);
    seatExtraSelect.on('change', updatePrice);

// Измените эту строку:
    $('.extra-checkbox').on('change', addNewCheckbox);

    $('body').on('change', '#id_row_letter, #id_seat_type, #id_extra, .extra-select', updatePrice);


    function sendPriceToServer(price) {
        $.ajax({
            type: 'POST',
            url: '/save_price/', // Замените на URL-адрес вашего представления
            data: {
                'price': price
            },
            success: function (response) {
                console.log("Цена успешно сохранена на сервере.");
            },
            error: function (error) {
                console.log("Ошибка при сохранении цены на сервере.");
            }
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    let csrftoken = getCookie('csrftoken');

    $.ajaxSetup({

        beforeSend: function (xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }

    });

});








