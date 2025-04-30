# main.py

import telebot
from telebot import types
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# === Загрузка переменных окружения ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("❌ TOKEN не найден. Проверь .env файл!")

bot = telebot.TeleBot(TOKEN)

# === Пути к файлам ===
ADS_FILE = "ads.json"
STATS_FILE = "stats.json"

# === Загрузка данных из файлов ===
if os.path.exists(ADS_FILE):
    with open(ADS_FILE, "r", encoding="utf-8") as f:
        ads = json.load(f)
else:
    ads = []

if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        stats = json.load(f)
else:
    stats = {"total_ads": 0, "total_views": 0}

ADMIN_ID = 123456789  # Замените на свой Telegram ID

# === Кнопки главного меню ===
def main_menu_buttons():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🚗 Купить авто"), types.KeyboardButton("🛒 Продать авто"))
    markup.add(types.KeyboardButton("💎 Премиум доступ"), types.KeyboardButton("📢 Наши партнёры"))
    markup.add(types.KeyboardButton("👨‍💻 Админ-панель"), types.KeyboardButton("🔙 В меню"))
    return markup

# === Команда /start ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}! Добро пожаловать в AutoBot Бишкек!",
        reply_markup=main_menu_buttons()
    )

# === Продажа авто ===
@bot.message_handler(func=lambda message: message.text == "🛒 Продать авто")
def sell_car_start(message):
    bot.send_message(message.chat.id, "Введите марку автомобиля:")
    bot.register_next_step_handler(message, get_make)

def get_make(message):
    user_data = {'user_id': message.chat.id}
    user_data['make'] = message.text
    bot.send_message(message.chat.id, "Введите модель автомобиля:")
    bot.register_next_step_handler(message, get_model, user_data)

def get_model(message, user_data):
    user_data['model'] = message.text
    bot.send_message(message.chat.id, "Введите год выпуска:")
    bot.register_next_step_handler(message, get_year, user_data)

def get_year(message, user_data):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректный год.")
        return bot.register_next_step_handler(message, get_year, user_data)
    user_data['year'] = message.text
    bot.send_message(message.chat.id, "Введите цену (в сомах):")
    bot.register_next_step_handler(message, get_price, user_data)

def get_price(message, user_data):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную цену.")
        return bot.register_next_step_handler(message, get_price, user_data)
    user_data['price'] = message.text
    bot.send_message(message.chat.id, "Введите контактный номер телефона:")
    bot.register_next_step_handler(message, get_contact, user_data)

def get_contact(message, user_data):
    user_data['contact'] = message.text
    bot.send_message(message.chat.id, "Прикрепите фото автомобиля (или напишите 'Пропустить'):")
    bot.register_next_step_handler(message, get_image, user_data)

def get_image(message, user_data):
    if message.text and message.text.lower() == 'пропустить':
        user_data['image'] = None
        proceed_to_finish(message, user_data)
    elif message.photo:
        user_data['image'] = message.photo[-1].file_id
        proceed_to_finish(message, user_data)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, прикрепите фото или напишите 'Пропустить'.")
        bot.register_next_step_handler(message, get_image, user_data)

def proceed_to_finish(message, user_data):
    user_data['date'] = datetime.now().isoformat()
    ads.append(user_data)
    with open(ADS_FILE, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)

    stats['total_ads'] += 1
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    bot.send_message(message.chat.id, "✅ Ваше объявление добавлено!", reply_markup=main_menu_buttons())

# === Покупка авто ===
@bot.message_handler(func=lambda message: message.text == "🚗 Купить авто")
def buy_car_start(message):
    available_makes = ', '.join(sorted(set(ad['make'] for ad in ads)))
    bot.send_message(message.chat.id, f"Введите интересующую марку (например, Toyota):\nДоступные марки: {available_makes}")
    bot.register_next_step_handler(message, filter_by_make)

def filter_by_make(message):
    make = message.text.lower()
    matching_ads = [ad for ad in ads if ad['make'].lower() == make]
    if not matching_ads:
        bot.send_message(message.chat.id, f"Нет объявлений по марке '{make}'.")
        return
    bot.send_message(message.chat.id, "Введите минимальный год выпуска (например, 2010):")
    bot.register_next_step_handler(message, filter_by_year, matching_ads)

def filter_by_year(message, matching_ads):
    try:
        min_year = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число (год).")
        return
    filtered = [ad for ad in matching_ads if ad['year'].isdigit() and int(ad['year']) >= min_year]
    if not filtered:
        bot.send_message(message.chat.id, "Нет подходящих объявлений по году.")
        return
    bot.send_message(message.chat.id, "Введите максимальную цену (в сомах):")
    bot.register_next_step_handler(message, filter_by_price, filtered)

def filter_by_price(message, filtered_ads):
    try:
        max_price = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число (цену).")
        return
    result_ads = [ad for ad in filtered_ads if ad['price'].isdigit() and int(ad['price']) <= max_price]
    if not result_ads:
        bot.send_message(message.chat.id, "Нет подходящих объявлений по цене.")
        return

    for ad in result_ads:
        text = f"🚘 {ad['make']} {ad['model']}\n📅 Год: {ad['year']}\n💰 Цена: {ad['price']} сом\n📞 Контакт: {ad['contact']}"
        if ad.get('image'):
            bot.send_photo(message.chat.id, ad['image'], caption=text)
        else:
            bot.send_message(message.chat.id, text)

    bot.send_message(message.chat.id, "Нажмите '🔙 В меню' для выхода", reply_markup=main_menu_buttons())

# === Вернуться в меню ===
@bot.message_handler(func=lambda message: message.text == "🔙 В меню")
def go_to_main_menu(message):
    start(message)

# === Удаление объявлений пользователя ===
@bot.message_handler(commands=['delmyads'])
def delete_my_ads(message):
    user_ads = [ad for ad in ads if ad['user_id'] == message.chat.id]
    if not user_ads:
        bot.send_message(message.chat.id, "У вас нет размещённых объявлений.")
        return
    ad_list = "\n".join([f"{i+1}. {ad['make']} {ad['model']} ({ad['year']})" for i, ad in enumerate(user_ads)])
    bot.send_message(message.chat.id, f"Ваши объявления:\n{ad_list}\nВведите номер объявления для удаления:")
    bot.register_next_step_handler(message, delete_ad, user_ads)

def delete_ad(message, user_ads):
    try:
        index = int(message.text) - 1
        if 0 <= index < len(user_ads):
            ads.remove(user_ads[index])
            with open(ADS_FILE, "w", encoding="utf-8") as f:
                json.dump(ads, f, ensure_ascii=False, indent=2)
            bot.send_message(message.chat.id, "✅ Объявление удалено!")
        else:
            bot.send_message(message.chat.id, "Некорректный номер объявления.")
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число.")

# === Премиум доступ ===
@bot.message_handler(func=lambda message: message.text == "💎 Премиум доступ")
def premium_access(message):
    bot.send_message(message.chat.id, "Премиум доступ позволяет быстрее продать или купить авто!\nСтоимость: 100 сомов/месяц.")

# === Админ-панель ===
@bot.message_handler(func=lambda message: message.text == "👨‍💻 Админ-панель")
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Вы не администратор.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🗑 Удалить все объявления"), types.KeyboardButton("📊 Статистика"))
    bot.send_message(message.chat.id, "Админ-панель", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🗑 Удалить все объявления")
def delete_all_ads(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Вы не администратор.")
        return
    global ads
    ads = []
    with open(ADS_FILE, "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=2)
    bot.send_message(message.chat.id, "Все объявления удалены.")

@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def show_stats(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Вы не администратор.")
        return
    bot.send_message(message.chat.id, f"Всего объявлений: {stats['total_ads']}\nВсего просмотров: {stats['total_views']}")


from waitress import serve
from flask import Flask
import threading


def run_flask():
    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Telegram Bot is running on Fly.io!"

    # Production-сервер
    serve(app, host="0.0.0.0", port=8080)


# Запускаем в отдельном потоке
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

print("🌐 Production server started on port 8080")
# === Конец изменений ===

# === Запуск бота ===
print("🤖 Бот успешно запущен...")
bot.infinity_polling()
try:
    bot.infinity_polling()
except Exception as e:
    print(f"❌ Ошибка бота: {e}")
    # Можно добавить перезапуск через 5 секунд