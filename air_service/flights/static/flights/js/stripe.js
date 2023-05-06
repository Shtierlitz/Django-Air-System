// Убедитесь, что jQuery и Stripe.js подключены к вашему проекту
$(document).ready(function() {
    const stripe = Stripe("pk_test_51MwUgUJhy2cy90iNKj5iKkjkcmbB3cRTdxcb7kUMPHweOF5UbO4GMdTAXM4ZPc94eVdJ4DrmprmMXpM7cayIpVBi00VJqZ5pP4");

    // Создайте экземпляр элемента карты Stripe
    const elements = stripe.elements();
    const card = elements.create('card');
    card.mount('#card-element');

    // Обработка событий ошибок ввода данных карты
    card.addEventListener('change', function(event) {
        const displayError = document.getElementById('card-errors');
        if (event.error) {
            displayError.textContent = event.error.message;
        } else {
            displayError.textContent = '';
        }
    });

    // Обработка события отправки формы оплаты
    const form = document.getElementById('payment-form');
    form.addEventListener('submit', function(event) {
        event.preventDefault();

        stripe.createToken(card).then(function(result) {
            if (result.error) {
                const errorElement = document.getElementById('card-errors');
                errorElement.textContent = result.error.message;
            } else {
                stripeTokenHandler(result.token);
            }
        });
    });

    function stripeTokenHandler(token) {
        // Вставьте скрытый токен ввода в форму, чтобы его можно было отправить серверу
        const form = document.getElementById('payment-form');
        const hiddenInput = document.createElement('input');
        hiddenInput.setAttribute('type', 'hidden');
        hiddenInput.setAttribute('name', 'stripeToken');
        hiddenInput.setAttribute('value', token.id);
        form.appendChild(hiddenInput);

        // Отправьте форму
        form.submit();
    }
});
