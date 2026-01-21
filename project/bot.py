import logging
import sqlite3
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # type: ignore
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes # type: ignore

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "7735533602:AAE560P1F7bRXDPr20o4VHUeQdWOUhEzSOg"

# Директория для хранения изображений
IMAGES_DIR = "product_images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# URL-адреса изображений для товаров (используем placeholder изображения)
IMAGE_URLS = {
    1: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop",
    2: "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=400&fit=crop",
    3: "https://images.unsplash.com/photo-1542272604-787c3835535d?w-400&h=500&fit=crop",
    4: "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop",
    5: "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400&h=500&fit=crop",
    6: "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop",
    7: "https://images.unsplash.com/photo-1588850561407-81b17e009b6d?w=400&h=400&fit=crop",
    8: "https://images.unsplash.com/photo-1624277904875-2f8e8577f393?w=400&h=400&fit=crop",
}

# Альтернативные ссылки на случай, если Unsplash недоступен
BACKUP_IMAGE_URLS = {
    1: "https://placehold.co/400x400/FF6B6B/FFFFFF?text=Basic+T-Shirt",
    2: "https://placehold.co/400x400/4ECDC4/FFFFFF?text=Premium+T-Shirt",
    3: "https://placehold.co/400x500/45B7D1/FFFFFF?text=Slim+Jeans",
    4: "https://placehold.co/400x500/96CEB4/FFFFFF?text=Oxford+Shirt",
    5: "https://placehold.co/400x500/FECA57/FFFFFF?text=Windbreaker",
    6: "https://placehold.co/400x400/FF9FF3/FFFFFF?text=Runner+Shoes",
    7: "https://placehold.co/400x400/54A0FF/FFFFFF?text=Classic+Cap",
    8: "https://placehold.co/400x400/5F27CD/FFFFFF?text=Leather+Belt",
}

# Константы
class ClothingCategory(Enum):
    TSHIRT = "Футболки"
    SHIRT = "Рубашки"
    PANTS = "Штаны/Джинсы"
    JACKET = "Куртки"
    SHOES = "Обувь"
    ACCESSORIES = "Аксессуары"

# ========== МОДЕЛЬ ДАННЫХ ==========

class ClothingItem:
    def __init__(self, id: int, name: str, category: ClothingCategory, 
                 price: float, description: str, stock: int = 100,
                 image_url: Optional[str] = None):
        self.id = id
        self.name = name
        self.category = category
        self.price = price
        self.description = description
        self.stock = stock
        self.image_url = image_url or IMAGE_URLS.get(id, BACKUP_IMAGE_URLS.get(id))

# Каталог одежды с изображениями
CLOTHING_CATALOG = [
    ClothingItem(1, "Футболка Basic", ClothingCategory.TSHIRT, 1499.99, 
                "Базовая хлопковая футболка отличного качества. Доступна в различных цветах.", 50),
    ClothingItem(2, "Футболка Premium", ClothingCategory.TSHIRT, 2999.99, 
                "Премиум футболка из органического хлопка. Экологично и комфортно.", 30),
    ClothingItem(3, "Джинсы Slim", ClothingCategory.PANTS, 4999.99, 
                "Стройные джинсы из премиального денима. Идеальная посадка.", 40),
    ClothingItem(4, "Рубашка Oxford", ClothingCategory.SHIRT, 3999.99, 
                "Классическая оксфордская рубашка для офиса и повседневной носки.", 25),
    ClothingItem(5, "Куртка Windbreaker", ClothingCategory.JACKET, 7999.99, 
                "Ветровка с мембраной для защиты от ветра и легкого дождя.", 20),
    ClothingItem(6, "Кроссовки Runner", ClothingCategory.SHOES, 5999.99, 
                "Беговые кроссовки с амортизацией для максимального комфорта.", 35),
    ClothingItem(7, "Кепка Classic", ClothingCategory.ACCESSORIES, 999.99, 
                "Бейсболка с регулируемым ремешком. Защита от солнца в стиле.", 60),
    ClothingItem(8, "Кожаный ремень", ClothingCategory.ACCESSORIES, 1999.99, 
                "Кожаный ремень с металлической пряжкой. Классика на каждый день.", 45),
]

# ========== БАЗА ДАННЫХ ==========

class Database:
    def __init__(self, db_name="bot_database.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.initialize_catalog()
    
    def create_tables(self):
        """Создание таблиц в базе данных"""
        # Таблица пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        
        # Проверяем наличие колонки balance и добавляем её если нужно
        self.cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        if 'balance' not in columns:
            logger.info("Добавляем колонку balance в таблицу users...")
            self.cursor.execute('ALTER TABLE users ADD COLUMN balance REAL DEFAULT 10000.00')
        
        # Проверяем наличие колонки notifications
        if 'notifications' not in columns:
            logger.info("Добавляем колонку notifications...")
            self.cursor.execute('ALTER TABLE users ADD COLUMN notifications INTEGER DEFAULT 1')
        
        # Таблица сохраненных имен
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_names (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                saved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица действий пользователя (логи)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица статистики нажатий кнопок
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS button_clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                button_id TEXT,
                click_count INTEGER DEFAULT 0,
                last_clicked TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица товаров (добавляем колонку image_url)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clothing_items (
                item_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                stock INTEGER DEFAULT 100,
                image_url TEXT
            )
        ''')
        
        # Проверяем наличие колонки image_url
        self.cursor.execute("PRAGMA table_info(clothing_items)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'image_url' not in columns:
            logger.info("Добавляем колонку image_url в таблицу clothing_items...")
            self.cursor.execute('ALTER TABLE clothing_items ADD COLUMN image_url TEXT')
        
        # Таблица корзины
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (item_id) REFERENCES clothing_items (item_id),
                UNIQUE(user_id, item_id)
            )
        ''')
        
        # Таблица заказов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица позиций заказа
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                item_id INTEGER,
                quantity INTEGER,
                price_per_item REAL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (item_id) REFERENCES clothing_items (item_id)
            )
        ''')
        
        # Таблица инвентаря пользователя
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 1,
                purchased_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (item_id) REFERENCES clothing_items (item_id)
            )
        ''')
        
        # Таблица избранных товаров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_id INTEGER,
                added_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (item_id) REFERENCES clothing_items (item_id),
                UNIQUE(user_id, item_id)
            )
        ''')
        
        self.conn.commit()
    
    def initialize_catalog(self):
        """Инициализация каталога товаров"""
        for item in CLOTHING_CATALOG:
            # Проверяем, существует ли уже товар
            self.cursor.execute('SELECT COUNT(*) FROM clothing_items WHERE item_id = ?', (item.id,))
            exists = self.cursor.fetchone()[0] > 0
            
            if not exists:
                self.cursor.execute('''
                    INSERT INTO clothing_items 
                    (item_id, name, category, price, description, stock, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (item.id, item.name, item.category.value, item.price, 
                      item.description, item.stock, item.image_url))
            else:
                # Обновляем существующий товар, добавляя image_url если нужно
                self.cursor.execute('''
                    UPDATE clothing_items 
                    SET image_url = ?
                    WHERE item_id = ? AND image_url IS NULL
                ''', (item.image_url, item.id))
        self.conn.commit()
    
    def add_or_update_user(self, user):
        """Добавление или обновление пользователя"""
        now = datetime.now()
        
        # Проверяем, существует ли пользователь
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', (user.id,))
        exists = self.cursor.fetchone()[0] > 0
        
        if exists:
            # Обновляем существующего пользователя
            self.cursor.execute('''
                UPDATE users 
                SET username = ?, first_name = ?, last_name = ?, last_seen = ?
                WHERE user_id = ?
            ''', (user.username, user.first_name, user.last_name, now, user.id))
        else:
            # Создаем нового пользователя с начальным балансом
            self.cursor.execute('''
                INSERT INTO users 
                (user_id, username, first_name, last_name, created_at, last_seen, balance, notifications)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user.id, user.username, user.first_name, user.last_name, now, now, 10000.00, 1))
        
        self.conn.commit()
    
    def log_action(self, user_id, action, details=""):
        """Логирование действий пользователя"""
        timestamp = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO user_actions (user_id, action, details, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, action, details, timestamp))
        self.conn.commit()
    
    def save_user_name(self, user_id, name):
        """Сохранение имени пользователя"""
        timestamp = datetime.now().isoformat()
        
        self.cursor.execute('DELETE FROM user_names WHERE user_id = ?', (user_id,))
        self.cursor.execute('''
            INSERT INTO user_names (user_id, name, saved_at)
            VALUES (?, ?, ?)
        ''', (user_id, name, timestamp))
        self.conn.commit()
        self.log_action(user_id, "set_name", f"Имя установлено: {name}")
    
    def get_user_name(self, user_id):
        """Получение сохраненного имени пользователя"""
        self.cursor.execute('SELECT name FROM user_names WHERE user_id = ? ORDER BY saved_at DESC LIMIT 1', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else "не установлено"
    
    def record_button_click(self, user_id, button_id):
        """Запись нажатия кнопки"""
        timestamp = datetime.now().isoformat()
        
        self.cursor.execute('''
            SELECT id, click_count FROM button_clicks 
            WHERE user_id = ? AND button_id = ?
        ''', (user_id, button_id))
        
        result = self.cursor.fetchone()
        
        if result:
            click_id, click_count = result
            self.cursor.execute('''
                UPDATE button_clicks 
                SET click_count = ?, last_clicked = ?
                WHERE id = ?
            ''', (click_count + 1, timestamp, click_id))
        else:
            self.cursor.execute('''
                INSERT INTO button_clicks (user_id, button_id, click_count, last_clicked)
                VALUES (?, ?, ?, ?)
            ''', (user_id, button_id, 1, timestamp))
        
        self.conn.commit()
    
    # ========== СИСТЕМА ПОКУПОК ==========
    
    def get_user_balance(self, user_id: int) -> float:
        """Получение баланса пользователя"""
        self.cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = self.cursor.fetchone()
        return float(result[0]) if result and result[0] is not None else 10000.00
    
    def update_user_balance(self, user_id: int, amount: float):
        """Обновление баланса пользователя"""
        self.cursor.execute('''
            UPDATE users 
            SET balance = COALESCE(balance, 10000.00) + ? 
            WHERE user_id = ?
        ''', (amount, user_id))
        self.conn.commit()
    
    def get_clothing_items(self, category: Optional[str] = None) -> List[Dict]:
        """Получение списка товаров"""
        if category:
            self.cursor.execute('''
                SELECT item_id, name, category, price, description, stock, image_url 
                FROM clothing_items 
                WHERE category = ? AND stock > 0
                ORDER BY price
            ''', (category,))
        else:
            self.cursor.execute('''
                SELECT item_id, name, category, price, description, stock, image_url 
                FROM clothing_items 
                WHERE stock > 0
                ORDER BY category, price
            ''')
        
        items = []
        for row in self.cursor.fetchall():
            items.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'price': float(row[3]) if row[3] else 0.0,
                'description': row[4],
                'stock': row[5],
                'image_url': row[6] or IMAGE_URLS.get(row[0], BACKUP_IMAGE_URLS.get(row[0]))
            })
        return items
    
    def get_item_details(self, item_id: int) -> Optional[Dict]:
        """Получение деталей товара"""
        self.cursor.execute('''
            SELECT item_id, name, category, price, description, stock, image_url 
            FROM clothing_items 
            WHERE item_id = ?
        ''', (item_id,))
        
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'price': float(row[3]) if row[3] else 0.0,
                'description': row[4],
                'stock': row[5],
                'image_url': row[6] or IMAGE_URLS.get(row[0], BACKUP_IMAGE_URLS.get(row[0]))
            }
        return None
    
    def add_to_cart(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        """Добавление товара в корзину"""
        # Проверяем наличие товара
        self.cursor.execute('SELECT stock FROM clothing_items WHERE item_id = ?', (item_id,))
        result = self.cursor.fetchone()
        
        if not result or result[0] < quantity:
            return False
        
        # Проверяем, есть ли уже товар в корзине
        self.cursor.execute('SELECT quantity FROM cart WHERE user_id = ? AND item_id = ?', (user_id, item_id))
        existing = self.cursor.fetchone()
        
        timestamp = datetime.now().isoformat()
        if existing:
            new_quantity = existing[0] + quantity
            if new_quantity > result[0]:
                return False
            self.cursor.execute('''
                UPDATE cart SET quantity = ?, added_at = ? 
                WHERE user_id = ? AND item_id = ?
            ''', (new_quantity, timestamp, user_id, item_id))
        else:
            self.cursor.execute('''
                INSERT INTO cart (user_id, item_id, quantity, added_at)
                VALUES (?, ?, ?, ?)
            ''', (user_id, item_id, quantity, timestamp))
        
        self.conn.commit()
        self.log_action(user_id, "add_to_cart", f"Item: {item_id}, Quantity: {quantity}")
        return True
    
    def get_cart(self, user_id: int) -> List[Dict]:
        """Получение содержимого корзины"""
        self.cursor.execute('''
            SELECT c.item_id, ci.name, ci.price, c.quantity, ci.stock, ci.image_url
            FROM cart c
            JOIN clothing_items ci ON c.item_id = ci.item_id
            WHERE c.user_id = ?
        ''', (user_id,))
        
        cart_items = []
        for row in self.cursor.fetchall():
            price = float(row[2]) if row[2] else 0.0
            quantity = row[3] if row[3] else 0
            cart_items.append({
                'item_id': row[0],
                'name': row[1],
                'price': price,
                'quantity': quantity,
                'stock': row[4],
                'image_url': row[5] or IMAGE_URLS.get(row[0], BACKUP_IMAGE_URLS.get(row[0])),
                'total': price * quantity
            })
        return cart_items
    
    def get_cart_total(self, user_id: int) -> float:
        """Получение общей суммы корзины"""
        self.cursor.execute('''
            SELECT SUM(ci.price * c.quantity)
            FROM cart c
            JOIN clothing_items ci ON c.item_id = ci.item_id
            WHERE c.user_id = ?
        ''', (user_id,))
        
        result = self.cursor.fetchone()
        return float(result[0]) if result and result[0] else 0.0
    
    def remove_from_cart(self, user_id: int, item_id: int):
        """Удаление товара из корзины"""
        self.cursor.execute('DELETE FROM cart WHERE user_id = ? AND item_id = ?', (user_id, item_id))
        self.conn.commit()
        self.log_action(user_id, "remove_from_cart", f"Item: {item_id}")
    
    def clear_cart(self, user_id: int):
        """Очистка корзины"""
        self.cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        self.conn.commit()
        self.log_action(user_id, "clear_cart")
    
    def place_order(self, user_id: int) -> Optional[int]:
        """Оформление заказа"""
        cart_items = self.get_cart(user_id)
        if not cart_items:
            return None
        
        total_amount = self.get_cart_total(user_id)
        balance = self.get_user_balance(user_id)
        
        if balance < total_amount:
            return None
        
        # Проверяем наличие товаров
        for item in cart_items:
            if item['quantity'] > item['stock']:
                return None
        
        # Создаем заказ
        timestamp = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT INTO orders (user_id, total_amount, status, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, total_amount, 'processing', timestamp))
        
        order_id = self.cursor.lastrowid
        
        # Добавляем товары в заказ и обновляем склад
        for item in cart_items:
            self.cursor.execute('''
                INSERT INTO order_items (order_id, item_id, quantity, price_per_item)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['item_id'], item['quantity'], item['price']))
            
            # Обновляем склад
            self.cursor.execute('''
                UPDATE clothing_items 
                SET stock = stock - ? 
                WHERE item_id = ?
            ''', (item['quantity'], item['item_id']))
        
        # Обновляем баланс
        self.cursor.execute('''
            UPDATE users 
            SET balance = COALESCE(balance, 10000.00) - ? 
            WHERE user_id = ?
        ''', (total_amount, user_id))
        
        # Добавляем товары в инвентарь пользователя
        for item in cart_items:
            # Проверяем, есть ли уже такой товар в инвентаре
            self.cursor.execute('''
                SELECT quantity FROM user_inventory 
                WHERE user_id = ? AND item_id = ?
            ''', (user_id, item['item_id']))
            
            existing = self.cursor.fetchone()
            if existing:
                new_quantity = existing[0] + item['quantity']
                self.cursor.execute('''
                    UPDATE user_inventory 
                    SET quantity = ?, purchased_at = ? 
                    WHERE user_id = ? AND item_id = ?
                ''', (new_quantity, timestamp, user_id, item['item_id']))
            else:
                self.cursor.execute('''
                    INSERT INTO user_inventory (user_id, item_id, quantity, purchased_at)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, item['item_id'], item['quantity'], timestamp))
        
        # Очищаем корзину
        self.clear_cart(user_id)
        
        # Обновляем статус заказа
        completed_timestamp = datetime.now().isoformat()
        self.cursor.execute('''
            UPDATE orders 
            SET status = 'completed', completed_at = ? 
            WHERE order_id = ?
        ''', (completed_timestamp, order_id))
        
        self.conn.commit()
        self.log_action(user_id, "place_order", f"Order ID: {order_id}, Amount: {total_amount}")
        return order_id
    
    def get_order_history(self, user_id: int) -> List[Dict]:
        """Получение истории заказов"""
        self.cursor.execute('''
            SELECT order_id, total_amount, status, created_at, completed_at
            FROM orders 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        orders = []
        for row in self.cursor.fetchall():
            orders.append({
                'order_id': row[0],
                'total_amount': float(row[1]) if row[1] else 0.0,
                'status': row[2],
                'created_at': row[3],
                'completed_at': row[4]
            })
        return orders
    
    def get_inventory(self, user_id: int) -> List[Dict]:
        """Получение инвентаря пользователя"""
        self.cursor.execute('''
            SELECT ui.item_id, ci.name, ci.category, ui.quantity, ui.purchased_at, ci.image_url
            FROM user_inventory ui
            JOIN clothing_items ci ON ui.item_id = ci.item_id
            WHERE ui.user_id = ?
            ORDER BY ui.purchased_at DESC
        ''', (user_id,))
        
        inventory = []
        for row in self.cursor.fetchall():
            inventory.append({
                'item_id': row[0],
                'name': row[1],
                'category': row[2],
                'quantity': row[3],
                'purchased_at': row[4],
                'image_url': row[5] or IMAGE_URLS.get(row[0], BACKUP_IMAGE_URLS.get(row[0]))
            })
        return inventory
    
    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        self.cursor.execute('SELECT COUNT(*) FROM user_names WHERE user_id = ?', (user_id,))
        names_count = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT SUM(click_count) FROM button_clicks WHERE user_id = ?', (user_id,))
        total_clicks_result = self.cursor.fetchone()
        total_clicks = total_clicks_result[0] if total_clicks_result and total_clicks_result[0] else 0
        
        self.cursor.execute('''
            SELECT button_id, click_count, last_clicked 
            FROM button_clicks 
            WHERE user_id = ? 
            ORDER BY click_count DESC
        ''', (user_id,))
        button_stats = self.cursor.fetchall()
        
        self.cursor.execute('SELECT created_at FROM users WHERE user_id = ?', (user_id,))
        created_at_result = self.cursor.fetchone()
        created_at = created_at_result[0] if created_at_result else None
        
        # Статистика покупок
        self.cursor.execute('SELECT COUNT(*), SUM(total_amount) FROM orders WHERE user_id = ?', (user_id,))
        order_stats = self.cursor.fetchone()
        orders_count = order_stats[0] if order_stats and order_stats[0] else 0
        total_spent = float(order_stats[1]) if order_stats and order_stats[1] else 0.0
        
        return {
            'names_count': names_count,
            'total_clicks': total_clicks,
            'button_stats': button_stats,
            'created_at': created_at,
            'orders_count': orders_count,
            'total_spent': total_spent,
            'balance': self.get_user_balance(user_id)
        }
    
    def get_all_users_count(self):
        """Получение общего количества пользователей"""
        self.cursor.execute('SELECT COUNT(*) FROM users')
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def get_random_item(self):
        """Получение случайного товара"""
        self.cursor.execute('''
            SELECT item_id, name, category, price, description, stock, image_url 
            FROM clothing_items 
            WHERE stock > 0
            ORDER BY RANDOM()
            LIMIT 1
        ''')
        
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'price': float(row[3]) if row[3] else 0.0,
                'description': row[4],
                'stock': row[5],
                'image_url': row[6] or IMAGE_URLS.get(row[0], BACKUP_IMAGE_URLS.get(row[0]))
            }
        return None
    
    def get_featured_items(self, limit: int = 3):
        """Получение рекомендуемых товаров"""
        self.cursor.execute('''
            SELECT item_id, name, category, price, description, stock, image_url 
            FROM clothing_items 
            WHERE stock > 0
            ORDER BY RANDOM()
            LIMIT ?
        ''', (limit,))
        
        items = []
        for row in self.cursor.fetchall():
            items.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'price': float(row[3]) if row[3] else 0.0,
                'description': row[4],
                'stock': row[5],
                'image_url': row[6] or IMAGE_URLS.get(row[0], BACKUP_IMAGE_URLS.get(row[0]))
            })
        return items
    
    def close(self):
        """Закрытие соединения с БД"""
        self.conn.close()

# Инициализация базы данных
db = Database()

# ========== КОМАНДЫ БОТА ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    db.add_or_update_user(user)
    db.log_action(user.id, "start_command")
    
    total_users = db.get_all_users_count()
    balance = db.get_user_balance(user.id)
    
    # Получаем рекомендуемые товары
    featured_items = db.get_featured_items(2)
    featured_text = ""
    if featured_items:
        featured_text = "\n🔥 *Рекомендуем к покупке:*\n"
        for item in featured_items:
            featured_text += f"• {item['name']} - {item['price']:.2f} руб.\n"
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"🛍️ *Добро пожаловать в магазин одежды!*\n\n"
        f"💰 Ваш баланс: *{balance:.2f} руб.*\n"
        f"👥 Всего пользователей: {total_users}"
        f"{featured_text}\n"
        f"📚 *Доступные команды:*\n"
        f"/start - начать работу\n"
        f"/shop - магазин одежды\n"
        f"/featured - рекомендуемые товары\n"
        f"/cart - корзина покупок\n"
        f"/orders - мои заказы\n"
        f"/inventory - мой инвентарь\n"
        f"/balance - баланс и пополнение\n"
        f"/stats - ваша статистика\n"
        f"/help - помощь",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    user = update.effective_user
    db.log_action(user.id, "help_command")
    
    help_text = """
🛍️ *Магазин одежды - Помощь*

*Основные команды:*
/shop - просмотреть каталог одежды
/featured - рекомендуемые товары
/cart - просмотреть корзину
/orders - история заказов
/inventory - ваш инвентарь
/balance - баланс и управление

*Управление аккаунтом:*
/setname [имя] - сохранить имя
/getname - показать сохраненное имя
/stats - статистика использования

*Как покупать:*
1. Зайдите в /shop или /featured
2. Выберите товар с изображением
3. Добавьте товары в корзину
4. Перейдите в /cart
5. Оформите заказ

💰 *Начальный баланс:* 10,000 руб.
📸 *Все товары с изображениями!*
💾 Все данные сохраняются в базе SQLite!
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def featured_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать рекомендуемые товары"""
    user = update.effective_user
    db.log_action(user.id, "featured_command")
    
    featured_items = db.get_featured_items(4)
    
    if not featured_items:
        await update.message.reply_text("😔 Пока нет рекомендуемых товаров.")
        return
    
    await update.message.reply_text("🔥 *Рекомендуемые товары:*\n", parse_mode='Markdown')
    
    for item in featured_items:
        keyboard = [
            [InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"add_{item['id']}"),
             InlineKeyboardButton("📖 Подробнее", callback_data=f"item_{item['id']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await update.message.reply_photo(
                photo=item['image_url'],
                caption=f"*{item['name']}*\n"
                       f"🏷️ Цена: *{item['price']:.2f} руб.*\n"
                       f"📦 В наличии: *{item['stock']} шт.*\n"
                       f"📋 Категория: {item['category']}\n\n"
                       f"{item['description'][:100]}...",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            await update.message.reply_text(
                f"*{item['name']}*\n"
                f"🏷️ Цена: *{item['price']:.2f} руб.*\n"
                f"📦 В наличии: *{item['stock']} шт.*\n"
                f"📋 Категория: {item['category']}\n\n"
                f"{item['description']}",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать магазин одежды"""
    user = update.effective_user
    db.log_action(user.id, "shop_command")
    
    keyboard = []
    for category in ClothingCategory:
        keyboard.append([InlineKeyboardButton(
            f"👕 {category.value}",
            callback_data=f"category_{category.name}"
        )])
    
    keyboard.append([
        InlineKeyboardButton("🔥 Рекомендуем", callback_data="featured"),
        InlineKeyboardButton("🎲 Случайный товар", callback_data="random_item")
    ])
    keyboard.append([
        InlineKeyboardButton("🛒 Корзина", callback_data="view_cart"),
        InlineKeyboardButton("💰 Баланс", callback_data="view_balance")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    balance = db.get_user_balance(user.id)
    
    if update.message:
        await update.message.reply_text(
            f"🛍️ *Магазин одежды*\n\n"
            f"📸 *Все товары с изображениями!*\n\n"
            f"Выберите категорию:\n"
            f"💰 Ваш баланс: *{balance:.2f} руб.*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(
            f"🛍️ *Магазин одежды*\n\n"
            f"📸 *Все товары с изображениями!*\n\n"
            f"Выберите категорию:\n"
            f"💰 Ваш баланс: *{balance:.2f} руб.*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # Если нет возможности отправить сообщение, пробуем через новый
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🛍️ *Магазин одежды*\n\nВыберите категорию:\n💰 Ваш баланс: *{balance:.2f} руб.*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: ClothingCategory):
    """Показать товары категории"""
    query = update.callback_query
    
    # Проверяем, существует ли query
    if not query or not query.message:
        logger.warning("Callback query или сообщение не найдены")
        return
    
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Не удалось ответить на callback: {e}")
    
    user = update.effective_user
    items = db.get_clothing_items(category.value)
    
    if not items:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_shop")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👕 *{category.value}*\n\n"
            f"Товары временно отсутствуют.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    # Создаем клавиатуру с товарами
    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} - {item['price']:.2f} руб.",
            callback_data=f"item_{item['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_shop")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"👕 *{category.value}*\n\n"
        f"Выберите товар для просмотра изображения и деталей:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def show_item_details(update: Update, context: ContextTypes.DEFAULT_TYPE, item_id: int):
    """Показать детали товара с изображением"""
    query = update.callback_query
    
    # Проверяем, существует ли query
    if not query:
        logger.warning("Callback query не найден")
        return
    
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Не удалось ответить на callback: {e}")
    
    user = update.effective_user
    item = db.get_item_details(item_id)
    
    if not item:
        if query.message:
            await query.edit_message_text("❌ Товар не найден.")
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"add_{item_id}")],
        [InlineKeyboardButton("🛒 В корзину", callback_data="view_cart"),
         InlineKeyboardButton("🔙 Назад", callback_data=f"category_{next(c for c in ClothingCategory if c.value == item['category']).name}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if query.message:
            await query.message.reply_photo(
                photo=item['image_url'],
                caption=f"*{item['name']}*\n"
                       f"🏷️ Цена: *{item['price']:.2f} руб.*\n"
                       f"📦 В наличии: *{item['stock']} шт.*\n"
                       f"📋 Категория: {item['category']}\n\n"
                       f"{item['description']}\n\n"
                       f"💰 Ваш баланс: *{db.get_user_balance(user.id):.2f} руб.*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            # Удаляем предыдущее сообщение
            await query.delete_message()
        else:
            if update.effective_chat:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=item['image_url'],
                    caption=f"*{item['name']}*\n"
                           f"🏷️ Цена: *{item['price']:.2f} руб.*\n"
                           f"📦 В наличии: *{item['stock']} шт.*\n"
                           f"📋 Категория: {item['category']}\n\n"
                           f"{item['description']}\n\n"
                           f"💰 Ваш баланс: *{db.get_user_balance(user.id):.2f} руб.*",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
    except Exception as e:
        logger.error(f"Ошибка при отправке фото товара: {e}")
        if query.message:
            await query.edit_message_text(
                f"*{item['name']}*\n"
                f"🏷️ Цена: *{item['price']:.2f} руб.*\n"
                f"📦 В наличии: *{item['stock']} шт.*\n"
                f"📋 Категория: {item['category']}\n\n"
                f"{item['description']}\n\n"
                f"💰 Ваш баланс: *{db.get_user_balance(user.id):.2f} руб.*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*{item['name']}*\n"
                     f"🏷️ Цена: *{item['price']:.2f} руб.*\n"
                     f"📦 В наличии: *{item['stock']} шт.*\n"
                     f"📋 Категория: {item['category']}\n\n"
                     f"{item['description']}\n\n"
                     f"💰 Ваш баланс: *{db.get_user_balance(user.id):.2f} руб.*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать корзину"""
    user = update.effective_user
    cart_items = db.get_cart(user.id)
    total = db.get_cart_total(user.id)
    balance = db.get_user_balance(user.id)
    
    if not cart_items:
        keyboard = [[InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                "🛒 *Ваша корзина пуста*\n\n"
                "Добавьте товары из магазина!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.edit_message_text(
                "🛒 *Ваша корзина пуста*\n\n"
                "Добавьте товары из магазина!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🛒 *Ваша корзина пуста*\n\nДобавьте товары из магазина!",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        return
    
    # Формируем сообщение с товарами
    cart_text = "🛒 *Ваша корзина:*\n\n"
    for item in cart_items:
        cart_text += f"• {item['name']}\n"
        cart_text += f"  Количество: {item['quantity']} × {item['price']:.2f} руб. = {item['total']:.2f} руб.\n\n"
    
    cart_text += f"💰 *Итого: {total:.2f} руб.*\n"
    cart_text += f"💳 *Баланс: {balance:.2f} руб.*\n\n"
    
    if balance >= total:
        cart_text += "✅ Достаточно средств для покупки"
    else:
        cart_text += "❌ Недостаточно средств. Пополните баланс!"
    
    # Создаем клавиатуру
    keyboard = []
    for item in cart_items:
        keyboard.append([
            InlineKeyboardButton(f"❌ {item['name'][:10]}...", callback_data=f"remove_{item['item_id']}"),
            InlineKeyboardButton(f"➕", callback_data=f"inc_{item['item_id']}"),
            InlineKeyboardButton(f"➖", callback_data=f"dec_{item['item_id']}")
        ])
    
    keyboard.append([InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")])
    keyboard.append([InlineKeyboardButton("🛍️ Продолжить покупки", callback_data="back_to_shop")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            cart_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(
            cart_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=cart_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю заказов"""
    user = update.effective_user
    orders = db.get_order_history(user.id)
    
    if not orders:
        keyboard = [[InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📦 *У вас пока нет заказов*\n\n"
            "Совершите первую покупку в магазине!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    orders_text = "📦 *История заказов:*\n\n"
    for order in orders:
        created_at = order['created_at']
        if created_at:
            try:
                if isinstance(created_at, str):
                    order_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    order_date = created_at
                date_str = order_date.strftime('%d.%m.%Y %H:%M')
            except:
                date_str = str(created_at)
        else:
            date_str = "неизвестно"
            
        orders_text += f"🔹 *Заказ #{order['order_id']}*\n"
        orders_text += f"💵 Сумма: {order['total_amount']:.2f} руб.\n"
        orders_text += f"📊 Статус: {order['status']}\n"
        orders_text += f"📅 Дата: {date_str}\n\n"
    
    keyboard = [[InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        orders_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def inventory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать инвентарь пользователя с изображениями"""
    user = update.effective_user
    inventory = db.get_inventory(user.id)
    
    if not inventory:
        keyboard = [[InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎒 *Ваш инвентарь пуст*\n\n"
            "Купите товары в магазине!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return
    
    await update.message.reply_text(
        f"🎒 *Ваш инвентарь:*\n\n"
        f"Всего предметов: {len(inventory)}\n",
        parse_mode='Markdown'
    )
    
    # Отправляем изображения товаров из инвентаря
    for item in inventory[:5]:  # Показываем первые 5
        purchased_at = item['purchased_at']
        if purchased_at:
            try:
                if isinstance(purchased_at, str):
                    purchase_date = datetime.fromisoformat(purchased_at.replace('Z', '+00:00'))
                else:
                    purchase_date = purchased_at
                date_str = purchase_date.strftime('%d.%m.%Y')
            except:
                date_str = str(purchased_at)
        else:
            date_str = "неизвестно"
            
        try:
            await update.message.reply_photo(
                photo=item['image_url'],
                caption=f"👕 *{item['name']}*\n"
                       f"📦 Количество: {item['quantity']} шт.\n"
                       f"🏷️ Категория: {item['category']}\n"
                       f"📅 Куплено: {date_str}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото из инвентаря: {e}")
            await update.message.reply_text(
                f"👕 *{item['name']}*\n"
                f"📦 Количество: {item['quantity']} шт.\n"
                f"🏷️ Категория: {item['category']}\n"
                f"📅 Куплено: {date_str}",
                parse_mode='Markdown'
            )
    
    if len(inventory) > 5:
        await update.message.reply_text(
            f"...и еще {len(inventory) - 5} товаров в вашем инвентаре."
        )
    
    keyboard = [[InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Что хотите сделать дальше?",
        reply_markup=reply_markup
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать баланс и управление"""
    user = update.effective_user
    balance = db.get_user_balance(user.id)
    
    keyboard = [
        [InlineKeyboardButton("💳 Пополнить +1000", callback_data="add_1000"),
         InlineKeyboardButton("💳 Пополнить +5000", callback_data="add_5000")],
        [InlineKeyboardButton("💳 Пополнить +10000", callback_data="add_10000")],
        [InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            f"💰 *Управление балансом*\n\n"
            f"💳 Текущий баланс: *{balance:.2f} руб.*\n\n"
            f"Выберите сумму для пополнения:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(
            f"💰 *Управление балансом*\n\n"
            f"💳 Текущий баланс: *{balance:.2f} руб.*\n\n"
            f"Выберите сумму для пополнения:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"💰 *Управление балансом*\n\n💳 Текущий баланс: *{balance:.2f} руб.*\n\nВыберите сумму для пополнения:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats для просмотра статистики"""
    user = update.effective_user
    stats = db.get_user_stats(user.id)
    
    created_at = stats['created_at']
    if created_at:
        try:
            if isinstance(created_at, str):
                reg_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                reg_date = created_at
            date_str = reg_date.strftime('%d.%m.%Y %H:%M')
        except:
            date_str = str(created_at)
    else:
        date_str = 'неизвестно'
    
    inventory_count = len(db.get_inventory(user.id))
    
    stats_text = f"""
📊 *Статистика профиля:*

👤 *Основное:*
• Имя: {user.first_name}
• ID: {user.id}
• Баланс: {stats['balance']:.2f} руб.
• Дата регистрации: {date_str}

🛍️ *Покупки:*
• Заказов: {stats['orders_count']}
• Всего потрачено: {stats['total_spent']:.2f} руб.
• Товаров в инвентаре: {inventory_count}
• Сохраненных имен: {stats['names_count']}
• Нажатий кнопок: {stats['total_clicks']}

💾 *База данных:* bot_database.db
📸 *Товаров с изображениями:* {len(CLOTHING_CATALOG)}
"""
    
    keyboard = [[InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=stats_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    
    # Проверяем, существует ли query
    if not query:
        logger.warning("Callback query не найден")
        return
    
    # Проверяем, существует ли message
    if not query.message:
        logger.warning("Сообщение callback_query не найдено")
        # Пробуем отправить сообщение через context.bot
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Не удалось обработать запрос. Пожалуйста, попробуйте еще раз."
            )
        return
    
    try:
        await query.answer()
    except Exception as e:
        logger.warning(f"Не удалось ответить на callback: {e}")
    
    user = update.effective_user
    if user:
        db.record_button_click(user.id, query.data)
    
    try:
        if query.data == "main_menu":
            if query.message:
                await query.message.reply_text(
                    "Возвращаемся в главное меню...",
                    parse_mode='Markdown'
                )
            await start(update, context)
        
        elif query.data == "back_to_shop":
            await shop(update, context)
        
        elif query.data == "featured":
            await featured_command(update, context)
        
        elif query.data == "random_item":
            item = db.get_random_item()
            if item:
                await show_item_details(update, context, item['id'])
            else:
                if query.message:
                    await query.message.reply_text("😔 Нет доступных товаров")
                await shop(update, context)
        
        elif query.data.startswith("category_"):
            category_name = query.data.split("_")[1]
            try:
                category = ClothingCategory[category_name]
                await show_category(update, context, category)
            except KeyError:
                if query.message:
                    await query.message.reply_text("❌ Категория не найдена")
                await shop(update, context)
        
        elif query.data.startswith("item_"):
            item_id = int(query.data.split("_")[1])
            await show_item_details(update, context, item_id)
        
        elif query.data.startswith("add_"):
            item_id = int(query.data.split("_")[1])
            if user and db.add_to_cart(user.id, item_id):
                await query.answer("✅ Товар добавлен в корзину!", show_alert=True)
                # Возвращаемся к товару
                await show_item_details(update, context, item_id)
            else:
                await query.answer("❌ Не удалось добавить товар. Проверьте наличие.", show_alert=True)
        
        elif query.data == "view_cart":
            await cart_command(update, context)
        
        elif query.data == "view_balance":
            if query.message:
                await balance_command(update, context)
        
        elif query.data.startswith("remove_"):
            item_id = int(query.data.split("_")[1])
            if user:
                db.remove_from_cart(user.id, item_id)
            await query.answer("🗑️ Товар удален из корзины")
            await cart_command(update, context)
        
        elif query.data.startswith("inc_"):
            item_id = int(query.data.split("_")[1])
            if user and db.add_to_cart(user.id, item_id, 1):
                await query.answer("➕ Количество увеличено")
            else:
                await query.answer("❌ Нельзя добавить больше товара")
            await cart_command(update, context)
        
        elif query.data.startswith("dec_"):
            item_id = int(query.data.split("_")[1])
            if user:
                cart = db.get_cart(user.id)
                for item in cart:
                    if item['item_id'] == item_id:
                        if item['quantity'] > 1:
                            # Уменьшаем количество
                            db.remove_from_cart(user.id, item_id)
                            db.add_to_cart(user.id, item_id, item['quantity'] - 1)
                            await query.answer("➖ Количество уменьшено")
                        else:
                            # Удаляем товар
                            db.remove_from_cart(user.id, item_id)
                            await query.answer("🗑️ Товар удален")
                        break
            await cart_command(update, context)
        
        elif query.data == "clear_cart":
            if user:
                db.clear_cart(user.id)
            await query.answer("🗑️ Корзина очищена")
            await cart_command(update, context)
        
        elif query.data == "checkout":
            if user:
                order_id = db.place_order(user.id)
                if order_id:
                    total = db.get_cart_total(user.id)
                    balance = db.get_user_balance(user.id)
                    
                    order_text = f"""
✅ *Заказ оформлен!*

📦 Номер заказа: #{order_id}
💰 Сумма: {total:.2f} руб.
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

🎒 Товары добавлены в ваш инвентарь.
💳 Новый баланс: {balance:.2f} руб.
"""
                    keyboard = [
                        [InlineKeyboardButton("🎒 Мой инвентарь", callback_data="inventory"),
                         InlineKeyboardButton("📦 Мои заказы", callback_data="orders")],
                        [InlineKeyboardButton("🛍️ Продолжить покупки", callback_data="back_to_shop")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        order_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    await query.answer("❌ Не удалось оформить заказ. Проверьте баланс и наличие товаров.", show_alert=True)
            else:
                await query.answer("❌ Пользователь не найден", show_alert=True)
        
        elif query.data == "inventory":
            if user:
                inventory = db.get_inventory(user.id)
                if inventory:
                    inventory_text = "🎒 *Ваш инвентарь:*\n\n"
                    for item in inventory[:5]:  # Показываем только первые 5
                        inventory_text += f"• {item['name']} ×{item['quantity']}\n"
                    
                    if len(inventory) > 5:
                        inventory_text += f"\n...и еще {len(inventory) - 5} товаров"
                    
                    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="view_cart")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        inventory_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    await query.answer("🎒 Ваш инвентарь пуст", show_alert=True)
            else:
                await query.answer("❌ Пользователь не найден", show_alert=True)
        
        elif query.data == "orders":
            if user:
                orders = db.get_order_history(user.id)
                if orders:
                    orders_text = "📦 *Последние заказы:*\n\n"
                    for order in orders[:3]:
                        orders_text += f"• #{order['order_id']} - {order['total_amount']:.2f} руб.\n"
                    
                    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="view_cart")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        orders_text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    await query.answer("📦 У вас нет заказов", show_alert=True)
            else:
                await query.answer("❌ Пользователь не найден", show_alert=True)
        
        elif query.data in ["add_1000", "add_5000", "add_10000"]:
            if user:
                amounts = {
                    "add_1000": 1000.0,
                    "add_5000": 5000.0,
                    "add_10000": 10000.0
                }
                amount = amounts.get(query.data, 1000.0)
                db.update_user_balance(user.id, amount)
                db.log_action(user.id, "add_balance", f"Amount: {amount}")
                
                new_balance = db.get_user_balance(user.id)
                await query.answer(f"✅ Баланс пополнен на {amount:.2f} руб.", show_alert=True)
                
                # Обновляем сообщение с балансом
                keyboard = [
                    [InlineKeyboardButton("💳 Пополнить +1000", callback_data="add_1000"),
                     InlineKeyboardButton("💳 Пополнить +5000", callback_data="add_5000")],
                    [InlineKeyboardButton("💳 Пополнить +10000", callback_data="add_10000")],
                    [InlineKeyboardButton("🛍️ В магазин", callback_data="back_to_shop"),
                     InlineKeyboardButton("📊 Статистика", callback_data="stats")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"💰 *Управление балансом*\n\n"
                    f"💳 Текущий баланс: *{new_balance:.2f} руб.*\n\n"
                    f"✅ Пополнено: *+{amount:.2f} руб.*\n\n"
                    f"Выберите сумму для пополнения:",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await query.answer("❌ Пользователь не найден", show_alert=True)
        
        elif query.data == "stats":
            if user:
                stats = db.get_user_stats(user.id)
                inventory_count = len(db.get_inventory(user.id)) if user else 0
                stats_text = f"""
📊 *Статистика:*

💰 Баланс: {stats['balance']:.2f} руб.
🛍️ Заказов: {stats['orders_count']}
💵 Потрачено: {stats['total_spent']:.2f} руб.
👕 В инвентаре: {inventory_count} позиций
"""
                
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="view_balance")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    stats_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await query.answer("❌ Пользователь не найден", show_alert=True)
    
    except Exception as e:
        logger.error(f"Ошибка в обработке callback: {e}")
        if query and query.message:
            try:
                await query.message.reply_text("❌ Произошла ошибка при обработке запроса.")
            except:
                pass  # Не можем отправить сообщение об ошибке

async def set_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение имени пользователя в БД"""
    user = update.effective_user
    
    if context.args:
        name = ' '.join(context.args)
        db.save_user_name(user.id, name)
        await update.message.reply_text(f"✅ Имя сохранено: *{name}*", parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "❌ Использование: /setname [ваше имя]\n"
            "Пример: /setname Виталий"
        )

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение сохраненного имени из БД"""
    user = update.effective_user
    name = db.get_user_name(user.id)
    await update.message.reply_text(f"📝 Ваше имя: *{name}*", parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка в обработчике: {context.error}", exc_info=True)
    
    # Логируем детали обновления для отладки
    if update:
        if update.message:
            logger.error(f"Ошибка в сообщении от пользователя {update.message.from_user.id}")
        elif update.callback_query:
            logger.error(f"Ошибка в callback от пользователя {update.callback_query.from_user.id}")
    
    # Пытаемся отправить сообщение об ошибке пользователю
    try:
        if update and update.effective_user:
            db.log_action(update.effective_user.id, "error", str(context.error))
            
            # Пытаемся отправить сообщение об ошибке
            error_text = "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз или начните с /start"
            
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(error_text)
            elif update.message:
                await update.message.reply_text(error_text)
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

def main():
    """Запуск бота"""
    print("🛍️ Запуск бота с магазином одежды...")
    print(f"💾 База данных: bot_database.db")
    print(f"👕 Категорий одежды: {len(CLOTHING_CATALOG)}")
    print(f"📸 Товаров с изображениями: {len(CLOTHING_CATALOG)}")
    print(f"💰 Начальный баланс: 10,000 руб.")
    print(f"🖼️  Директория для изображений: {IMAGES_DIR}")
    
    try:
        application = Application.builder().token(TOKEN).build()

        # Регистрация команд магазина
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("shop", shop))
        application.add_handler(CommandHandler("featured", featured_command))
        application.add_handler(CommandHandler("cart", cart_command))
        application.add_handler(CommandHandler("orders", orders_command))
        application.add_handler(CommandHandler("inventory", inventory_command))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("setname", set_name))
        application.add_handler(CommandHandler("getname", get_name))
        
        # Обработчик callback-запросов
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        print("\n✅ Бот запущен успешно!")
        print("🛍️  Доступные команды:")
        print("  /shop - магазин одежды с изображениями")
        print("  /featured - рекомендуемые товары")
        print("  /cart - корзина покупок")
        print("  /orders - история заказов")
        print("  /inventory - ваш инвентарь (с картинками)")
        print("  /balance - баланс и пополнение")
        print("  /stats - статистика")
        print("\n📸 Теперь все товары отображаются с изображениями!")
        print("⏹️  Нажмите Ctrl+C для остановки")
        
        application.run_polling()
        
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
    finally:
        db.close()
        print("💾 Соединение с базой данных закрыто")

if __name__ == '__main__':
    main()