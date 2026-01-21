console.log("💳 Страница оплаты загружена");

// Данные для примера
const orderItems = [
    { id: 1, name: "Джинсы классические", price: 3490, quantity: 1, image: "https://via.placeholder.com/80/6a11cb/ffffff?text=Джинсы" },
    { id: 3, name: "Футболка с принтом", price: 1290, quantity: 2, image: "https://via.placeholder.com/80/ff6b6b/ffffff?text=Футболка" }
];

let deliveryCost = 300;
let discount = 500;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    console.log("💳 Инициализация страницы оплаты");
    
    loadOrderItems();
    updateOrderSummary();
    setupEventListeners();
    
    // Загружаем сохраненные данные из localStorage
    loadSavedData();
});

// Загрузка товаров в заказ
function loadOrderItems() {
    const orderItemsContainer = document.getElementById('orderItems');
    
    // Проверяем, есть ли сохраненные товары в localStorage
    const savedCart = localStorage.getItem('fashionStoreCart');
    if (savedCart) {
        const cart = JSON.parse(savedCart);
        if (cart.length > 0) {
            orderItemsContainer.innerHTML = '';
            cart.forEach(item => {
                const itemElement = document.createElement('div');
                itemElement.className = 'order-item';
                itemElement.innerHTML = `
                    <div class="item-info">
                        <span class="item-name">${item.name}</span>
                        <span class="item-price">${item.price.toLocaleString()} ₽ × ${item.quantity}</span>
                    </div>
                    <span class="item-total">${(item.price * item.quantity).toLocaleString()} ₽</span>
                `;
                orderItemsContainer.appendChild(itemElement);
            });
            return;
        }
    }
    
    // Если нет сохраненных данных, показываем пример
    orderItemsContainer.innerHTML = '';
    orderItems.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'order-item';
        itemElement.innerHTML = `
            <div class="item-info">
                <span class="item-name">${item.name}</span>
                <span class="item-price">${item.price.toLocaleString()} ₽ × ${item.quantity}</span>
            </div>
            <span class="item-total">${(item.price * item.quantity).toLocaleString()} ₽</span>
        `;
        orderItemsContainer.appendChild(itemElement);
    });
}

// Обновление сводки заказа
function updateOrderSummary() {
    // Считаем сумму товаров
    let itemsTotal = 0;
    const savedCart = localStorage.getItem('fashionStoreCart');
    
    if (savedCart) {
        const cart = JSON.parse(savedCart);
        itemsTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    } else {
        itemsTotal = orderItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    }
    
    // Обновляем стоимость доставки
    const deliveryMethod = document.querySelector('input[name="delivery"]:checked').value;
    switch(deliveryMethod) {
        case 'courier':
            deliveryCost = 300;
            break;
        case 'pickup':
            deliveryCost = 0;
            break;
        case 'post':
            deliveryCost = 200;
            break;
    }
    
    const grandTotal = itemsTotal + deliveryCost - discount;
    
    // Обновляем UI
    document.getElementById('itemsTotal').textContent = `${itemsTotal.toLocaleString()} ₽`;
    document.getElementById('deliveryCost').textContent = `${deliveryCost.toLocaleString()} ₽`;
    document.getElementById('grandTotal').textContent = `${grandTotal.toLocaleString()} ₽`;
}

// Настройка обработчиков событий
function setupEventListeners() {
    console.log("🔧 Настройка обработчиков оплаты");
    
    // Мобильное меню
    const menuToggle = document.getElementById('menuToggle');
    const closeMenu = document.getElementById('closeMenu');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            mobileMenu.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }
    
    if (closeMenu) {
        closeMenu.addEventListener('click', function() {
            mobileMenu.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Обновление стоимости при изменении способа доставки
    document.querySelectorAll('input[name="delivery"]').forEach(radio => {
        radio.addEventListener('change', updateOrderSummary);
    });
    
    // Показ/скрытие данных карты
    document.querySelectorAll('input[name="payment"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const cardDetails = document.getElementById('cardDetails');
            if (this.value === 'card') {
                cardDetails.style.display = 'block';
            } else {
                cardDetails.style.display = 'none';
            }
        });
    });
    
    // Применение промокода
    const applyPromoBtn = document.getElementById('applyPromo');
    if (applyPromoBtn) {
        applyPromoBtn.addEventListener('click', applyPromoCode);
    }
    
    // Валидация ввода данных карты
    const cardNumber = document.getElementById('cardNumber');
    if (cardNumber) {
        cardNumber.addEventListener('input', formatCardNumber);
    }
    
    const cardExpiry = document.getElementById('cardExpiry');
    if (cardExpiry) {
        cardExpiry.addEventListener('input', formatCardExpiry);
    }
    
    // Обработка оплаты
    const payBtn = document.getElementById('payBtn');
    if (payBtn) {
        payBtn.addEventListener('click', processPayment);
    }
    
    // Модальное окно
    const closeModal = document.getElementById('closeModal');
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            document.getElementById('successModal').style.display = 'none';
        });
    }
    
    const trackOrderBtn = document.getElementById('trackOrder');
    if (trackOrderBtn) {
        trackOrderBtn.addEventListener('click', function() {
            alert('Функция отслеживания заказа будет доступна после отправки товара. Номер для отслеживания: #ORD-2024-78945');
        });
    }
    
    // Сохранение данных формы
    const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]');
    formInputs.forEach(input => {
        input.addEventListener('blur', saveFormData);
    });
}

// Форматирование номера карты
function formatCardNumber(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{4})/g, '$1 ').trim();
    e.target.value = value.substring(0, 19);
}

// Форматирование срока действия карты
function formatCardExpiry(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length >= 2) {
        value = value.substring(0, 2) + '/' + value.substring(2, 4);
    }
    e.target.value = value.substring(0, 5);
}

// Применение промокода
function applyPromoCode() {
    const promoCode = document.getElementById('promoCode').value.toUpperCase();
    const discountElement = document.getElementById('discount');
    
    const validPromoCodes = {
        'FASHION2024': 1000,
        'SALE10': 500,
        'NEWUSER': 300
    };
    
    if (validPromoCodes[promoCode]) {
        discount = validPromoCodes[promoCode];
        discountElement.textContent = `-${discount.toLocaleString()} ₽`;
        discountElement.style.color = '#28a745';
        showMessage(`✅ Промокод применен! Скидка ${discount} ₽`);
        updateOrderSummary();
    } else if (promoCode === '') {
        showMessage('⚠️ Введите промокод');
    } else {
        discount = 0;
        discountElement.textContent = '0 ₽';
        discountElement.style.color = '';
        showMessage('❌ Промокод недействителен');
        updateOrderSummary();
    }
}

// Обработка оплаты
function processPayment(e) {
    e.preventDefault();
    
    console.log("💳 Обработка оплаты...");
    
    // Валидация формы
    if (!validateForm()) {
        return;
    }
    
    // Показать загрузку
    const payBtn = document.getElementById('payBtn');
    const originalText = payBtn.textContent;
    payBtn.textContent = 'Обработка...';
    payBtn.disabled = true;
    
    // Имитация обработки платежа
    setTimeout(() => {
        // Очищаем корзину
        localStorage.removeItem('fashionStoreCart');
        
        // Показываем модальное окно успеха
        document.getElementById('successModal').style.display = 'flex';
        
        // Восстанавливаем кнопку
        payBtn.textContent = originalText;
        payBtn.disabled = false;
        
        // Очищаем форму
        clearFormData();
        
        console.log("✅ Оплата успешно обработана");
    }, 2000);
}

// Валидация формы
function validateForm() {
    const requiredFields = ['name', 'email', 'phone', 'address'];
    let isValid = true;
    
    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (!field.value.trim()) {
            field.style.borderColor = '#dc3545';
            isValid = false;
            showMessage(`⚠️ Пожалуйста, заполните поле: ${field.previousElementSibling.textContent}`);
        } else {
            field.style.borderColor = '';
        }
    });
    
    // Проверка email
    const email = document.getElementById('email');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email.value && !emailRegex.test(email.value)) {
        email.style.borderColor = '#dc3545';
        isValid = false;
        showMessage('⚠️ Введите корректный email адрес');
    }
    
    // Проверка согласия с условиями
    const terms = document.getElementById('terms');
    if (!terms.checked) {
        showMessage('⚠️ Необходимо согласиться с условиями обработки данных');
        isValid = false;
    }
    
    return isValid;
}

// Сохранение данных формы
function saveFormData() {
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        address: document.getElementById('address').value,
        city: document.getElementById('city').value,
        zip: document.getElementById('zip').value
    };
    
    localStorage.setItem('paymentFormData', JSON.stringify(formData));
}

// Загрузка сохраненных данных
function loadSavedData() {
    const savedData = localStorage.getItem('paymentFormData');
    if (savedData) {
        const formData = JSON.parse(savedData);
        Object.keys(formData).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = formData[key];
            }
        });
    }
}

// Очистка данных формы
function clearFormData() {
    localStorage.removeItem('paymentFormData');
    
    // Сбрасываем форму
    document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]').forEach(input => {
        input.value = '';
    });
    
    // Сбрасываем чекбоксы
    document.getElementById('terms').checked = false;
    document.getElementById('newsletter').checked = false;
}

// Показать сообщение
function showMessage(text) {
    // Удаляем предыдущие сообщения
    const existingMessage = document.querySelector('.message-notification');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const message = document.createElement('div');
    message.className = 'message-notification';
    message.textContent = text;
    message.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #6a11cb;
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: fadeIn 0.3s, fadeOut 0.3s 2.7s;
        max-width: 300px;
    `;
    
    document.body.appendChild(message);
    
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 3000);
}

// Добавляем стили для анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
    }
    
    .modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.3s;
    }
    
    .modal-content {
        background: white;
        border-radius: 15px;
        max-width: 500px;
        width: 90%;
        max-height: 90vh;
        overflow-y: auto;
        animation: slideIn 0.3s;
    }
    
    @keyframes slideIn {
        from { transform: translateY(-50px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
`;
document.head.appendChild(style);