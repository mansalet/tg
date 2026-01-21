console.log("📱 Адаптивный скрипт загружен!");

// Проверка мобильного устройства
const isMobile = () => {
    return window.innerWidth <= 768;
};

// Проверка сенсорного экрана
const isTouchDevice = () => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    console.log("📱 DOM загружен! Мобильный:", isMobile(), "Сенсорный:", isTouchDevice());
    
    setupMobileMenu();
    setupEventListeners();
    setupResponsiveFeatures();
    setupTouchOptimizations();
    
    // Обновляем при изменении размера окна
    window.addEventListener('resize', handleResize);
});

// Настройка мобильного меню
function setupMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const closeMenu = document.getElementById('closeMenu');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (!menuToggle || !mobileMenu) {
        console.warn("Элементы мобильного меню не найдены");
        return;
    }
    
    // Создаем overlay для мобильного меню
    let overlay = document.querySelector('.mobile-menu-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'mobile-menu-overlay';
        document.body.appendChild(overlay);
    }
    
    // Открытие меню
    menuToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        openMobileMenu();
    });
    
    // Закрытие меню
    closeMenu.addEventListener('click', closeMobileMenu);
    overlay.addEventListener('click', closeMobileMenu);
    
    // Закрытие при клике на ссылку
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', function() {
            setTimeout(closeMobileMenu, 300); // Задержка для перехода
        });
    });
    
    // Закрытие при нажатии Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
        }
    });
    
    function openMobileMenu() {
        mobileMenu.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        menuToggle.style.display = 'none';
        console.log("📱 Мобильное меню открыто");
    }
    
    function closeMobileMenu() {
        mobileMenu.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        menuToggle.style.display = 'flex';
        console.log("📱 Мобильное меню закрыто");
    }
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Кнопка корзины
    const cartBtn = document.getElementById('cartBtn');
    if (cartBtn) {
        if (isTouchDevice()) {
            cartBtn.addEventListener('touchstart', function(e) {
                this.style.transform = 'scale(0.95)';
            }, { passive: true });
            
            cartBtn.addEventListener('touchend', function(e) {
                this.style.transform = '';
                handleCartClick();
            }, { passive: true });
        } else {
            cartBtn.addEventListener('click', handleCartClick);
        }
    }
    
    // Кнопки "В корзину"
    const addToCartBtns = document.querySelectorAll('.btn.small');
    addToCartBtns.forEach(btn => {
        if (isTouchDevice()) {
            btn.addEventListener('touchstart', function(e) {
                this.style.transform = 'scale(0.95)';
            }, { passive: true });
            
            btn.addEventListener('touchend', function(e) {
                this.style.transform = '';
                handleAddToCart(this);
            }, { passive: true });
        } else {
            btn.addEventListener('click', function() {
                handleAddToCart(this);
            });
        }
    });
    
    // Основные кнопки
    const mainButtons = document.querySelectorAll('.btn:not(.small)');
    mainButtons.forEach(btn => {
        if (isTouchDevice()) {
            btn.addEventListener('touchstart', function(e) {
                this.style.transform = 'translateY(-1px)';
            }, { passive: true });
            
            btn.addEventListener('touchend', function(e) {
                this.style.transform = '';
            }, { passive: true });
        }
    });
    
    // Обработка ссылок
    const links = document.querySelectorAll('a[href^="#"]:not([href="#"])');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                smoothScrollTo(targetElement);
            }
        });
    });
}

// Обработка добавления в корзину
function handleAddToCart(button) {
    const productElement = button.closest('.product');
    if (!productElement) return;
    
    const productName = productElement.querySelector('h3').textContent;
    const productPrice = productElement.querySelector('p').textContent;
    
    showNotification(`✅ ${productName} добавлен в корзину!`);
    
    // Обновляем счетчик корзины
    updateCartCount();
    
    // Анимация кнопки
    button.textContent = '✓ В корзине';
    button.style.background = '#28a745';
    button.disabled = true;
    
    setTimeout(() => {
        button.textContent = 'В корзину';
        button.style.background = '';
        button.disabled = false;
    }, 2000);
    
    console.log(`🛒 Добавлен товар: ${productName} за ${productPrice}`);
}

// Обработка клика по корзине
function handleCartClick() {
    if (isMobile()) {
        // На мобильных показываем простой попап
        showNotification('🛒 Корзина пока в разработке. Товары добавлены!');
    } else {
        alert('🛒 Корзина пока в разработке. Товары добавлены!');
    }
}

// Обновление счетчика корзины
function updateCartCount() {
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        let count = parseInt(cartCount.textContent) || 0;
        count++;
        cartCount.textContent = count;
        
        // Анимация счетчика
        cartCount.style.transform = 'scale(1.5)';
        setTimeout(() => {
            cartCount.style.transform = 'scale(1)';
        }, 300);
    }
}

// Показ уведомления
function showNotification(message) {
    // Удаляем старое уведомление
    const oldNotification = document.querySelector('.notification');
    if (oldNotification) {
        oldNotification.remove();
    }
    
    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Удаляем через 3 секунды
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// Плавная прокрутка
function smoothScrollTo(element) {
    const headerHeight = document.querySelector('.header').offsetHeight;
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerHeight;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

// Настройка адаптивных функций
function setupResponsiveFeatures() {
    // Добавляем классы для адаптивности
    if (isMobile()) {
        document.body.classList.add('mobile-view');
        document.body.classList.remove('desktop-view');
        
        // Улучшаем отображение карточек товаров
        const products = document.querySelectorAll('.product');
        products.forEach(product => {
            product.classList.add('mobile-card');
        });
    } else {
        document.body.classList.add('desktop-view');
        document.body.classList.remove('mobile-view');
    }
    
    // Оптимизация для Retina дисплеев
    if (window.devicePixelRatio > 1) {
        document.body.classList.add('retina');
    }
}

// Оптимизации для сенсорных экранов
function setupTouchOptimizations() {
    if (!isTouchDevice()) return;
    
    console.log("📱 Настройка оптимизаций для сенсорных экранов");
    
    // Увеличиваем зоны клика
    const touchElements = document.querySelectorAll('.btn, .nav-list a, .product');
    touchElements.forEach(element => {
        element.classList.add('touch-optimized');
    });
    
    // Отключаем ховер-эффекты на сенсорных устройствах
    const style = document.createElement('style');
    style.textContent = `
        @media (hover: none) and (pointer: coarse) {
            .btn:hover, .nav-list a:hover, .product:hover {
                transform: none !important;
                box-shadow: none !important;
            }
        }
    `;
    document.head.appendChild(style);
}

// Обработка изменения размера окна
function handleResize() {
    console.log("📱 Размер окна изменился:", window.innerWidth, '×', window.innerHeight);
    
    setupResponsiveFeatures();
    
    // Перестраиваем меню при переходе между мобильным и десктопом
    const mobileMenu = document.getElementById('mobileMenu');
    const overlay = document.querySelector('.mobile-menu-overlay');
    
    if (window.innerWidth > 768) {
        // На десктопе закрываем мобильное меню
        if (mobileMenu) {
            mobileMenu.classList.remove('active');
        }
        if (overlay) {
            overlay.classList.remove('active');
        }
        document.body.style.overflow = '';
    }
}

// Добавляем обработчики для форм (если есть)
function setupForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (isMobile()) {
                // На мобильных скрываем клавиатуру после отправки
                setTimeout(() => {
                    document.activeElement.blur();
                }, 100);
            }
        });
    });
    
    // Оптимизация полей ввода для мобильных
    const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            if (isMobile()) {
                // Прокручиваем к полю ввода
                setTimeout(() => {
                    this.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            }
        });
    });
}

// Инициализация при полной загрузке страницы
window.addEventListener('load', function() {
    console.log("📱 Страница полностью загружена");
    
    // Показываем контент с анимацией
    document.body.classList.add('loaded');
    
    // Инициализация форм
    setupForms();
    
    // Для мобильных: предотвращаем масштабирование при фокусе
    if (isMobile()) {
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        }
    }
});

// Добавляем стили для загрузки
const loadingStyles = document.createElement('style');
loadingStyles.textContent = `
    body {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    body.loaded {
        opacity: 1;
    }
    
    .mobile-card {
        margin: 10px;
    }
    
    .touch-optimized {
        min-height: 44px;
        cursor: pointer;
    }
    
    @media (max-width: 768px) {
        .product h3 {
            font-size: 16px;
        }
        
        .btn {
            width: 100%;
            max-width: 300px;
            margin-left: auto;
            margin-right: auto;
        }
    }
    
    @media (max-width: 480px) {
        .container {
            padding-left: 10px;
            padding-right: 10px;
        }
        
        .hero h1 {
            font-size: 24px;
        }
        
        .hero p {
            font-size: 16px;
        }
    }
`;
document.head.appendChild(loadingStyles);

// Экспортируем функции для глобального использования
window.FashionStore = {
    isMobile,
    isTouchDevice,
    showNotification,
    updateCartCount
};

console.log("✅ Адаптивный скрипт инициализирован");
// Добавляем к существующему скрипту

// Предзагрузка критических изображений
function preloadCriticalImages() {
    const criticalImages = [
        'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80',
        'https://images.unsplash.com/photo-1542272604-787c3835535d?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80'
    ];
    
    criticalImages.forEach(src => {
        const img = new Image();
        img.src = src;
    });
}

// Ленивая загрузка изображений
function setupLazyLoading() {
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('.product-image[loading="lazy"]');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                    
                    // Добавляем плавное появление
                    img.style.opacity = '0';
                    img.style.transition = 'opacity 0.5s ease';
                    
                    img.onload = function() {
                        img.style.opacity = '1';
                    };
                }
            });
        });
        
        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Оптимизация изображений для мобильных
function optimizeImagesForMobile() {
    if (window.innerWidth <= 768) {
        const images = document.querySelectorAll('.product-image');
        images.forEach(img => {
            // Можно добавить параметры для оптимизации изображений
            if (img.src.includes('unsplash.com')) {
                // Для Unsplash добавляем параметры для мобильных
                if (!img.src.includes('w=500')) {
                    img.src = img.src.replace(/\?.*$/, '') + '?auto=format&fit=crop&w=400&q=70';
                }
            }
        });
    }
}

// Инициализация в DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // ... существующий код ...
    
    // Добавляем новые функции
    preloadCriticalImages();
    setupLazyLoading();
    optimizeImagesForMobile();
    
    // Обработчик для кнопок добавления в корзину
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            handleAddToCartWithImage(this);
        });
    });
});

// Улучшенная обработка добавления в корзину с изображением
function handleAddToCartWithImage(button) {
    const productElement = button.closest('.product');
    if (!productElement) return;
    
    const productName = productElement.querySelector('h3').textContent;
    const productPrice = productElement.querySelector('.price').textContent;
    const productImage = productElement.querySelector('.product-image').src;
    
    // Анимация добавления
    animateAddToCart(button, productImage);
    
    // Обновляем корзину
    updateCartCount();
    
    // Показываем уведомление
    showNotification(`✅ ${productName} добавлен в корзину!`);
    
    console.log(`🛒 Добавлен товар: ${productName} за ${productPrice}`);
}

// Анимация добавления в корзину
function animateAddToCart(button, imageSrc) {
    // Сохраняем оригинальный текст
    const originalText = button.innerHTML;
    
    // Меняем текст и цвет
    button.innerHTML = '✓ Добавлено';
    button.style.background = '#28a745';
    button.disabled = true;
    
    // Создаем миниатюру изображения для анимации
    if (imageSrc && window.innerWidth > 768) {
        const imgClone = document.createElement('div');
        imgClone.style.cssText = `
            position: fixed;
            width: 50px;
            height: 50px;
            background-image: url(${imageSrc});
            background-size: cover;
            background-position: center;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            z-index: 1000;
            pointer-events: none;
            transition: all 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        `;
        
        const buttonRect = button.getBoundingClientRect();
        const cartBtn = document.querySelector('.cart-btn');
        const cartRect = cartBtn.getBoundingClientRect();
        
        imgClone.style.left = `${buttonRect.left + buttonRect.width/2 - 25}px`;
        imgClone.style.top = `${buttonRect.top + buttonRect.height/2 - 25}px`;
        
        document.body.appendChild(imgClone);
        
        // Анимация к корзине
        requestAnimationFrame(() => {
            imgClone.style.left = `${cartRect.left + cartRect.width/2 - 25}px`;
            imgClone.style.top = `${cartRect.top + cartRect.height/2 - 25}px`;
            imgClone.style.transform = 'scale(0.5) rotate(360deg)';
            imgClone.style.opacity = '0.5';
        });
        
        // Удаляем после анимации
        setTimeout(() => {
            imgClone.remove();
        }, 800);
    }
    
    // Восстанавливаем кнопку через 2 секунды
    setTimeout(() => {
        button.innerHTML = originalText;
        button.style.background = '';
        button.disabled = false;
    }, 2000);
}

// Обновляем функцию showNotification для лучшего отображения
function showNotification(message) {
    // Удаляем старое уведомление
    const oldNotification = document.querySelector('.notification');
    if (oldNotification) {
        oldNotification.remove();
    }
    
    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="font-size: 20px;">✅</div>
            <div>${message}</div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Автоматическое скрытие
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'fadeOut 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        }
    }, 3000);
    
    // Возможность закрыть вручную
    notification.addEventListener('click', function() {
        this.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => this.remove(), 300);
    });
}

// Добавляем стили для улучшенных уведомлений
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        color: #333;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        border-left: 5px solid #28a745;
        cursor: pointer;
        max-width: 350px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    @media (max-width: 768px) {
        .notification {
            top: 10px;
            right: 10px;
            left: 10px;
            max-width: none;
            text-align: center;
        }
    }
`;
document.head.appendChild(notificationStyles);