from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from db.create_db import create_db
from db.storage import get_devices
from globs import DB_PATH
from logger_config import setup_logger

logger = setup_logger(__file__)


# База данных устройств (в реальном проекте используй SQLite или другую БД)
# devices = [
#     {"id": 1, "name": "Dell XPS 13", "serial": "A1B2", "room": "Кабинет 101"},
#     {"id": 2, "name": "MacBook Pro", "serial": "C3D4", "room": "Кабинет 205"},
#     {"id": 3, "name": "Lenovo ThinkPad", "serial": "E5F6", "room": "Переговорная 3"},
#     {"id": 4, "name": "HP EliteBook", "serial": "G7H8", "room": "Кабинет 101"},
#     {"id": 5, "name": "Asus ZenBook", "serial": "I9J0", "room": "Кабинет 205"}
# ]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
👋 Привет! Я бот для учета ноутбуков.

Доступные команды:
/start - показать это сообщение
/devices - показать список устройств
/help - помощь
"""
    await update.message.reply_text(welcome_text)

# Команда /devices - показывает таблицу с кнопками
async def show_devices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаем заголовок таблицы
    table_header = "📋 Список ноутбуков:\n\n"
    table_header += "│ Название │ Серийный │ Комната │\n"
    table_header += "├──────────┼──────────┼──────────┤\n"
    
    # Формируем строки таблицы
    table_rows = []
    devices = get_devices(DB_PATH)
    for device in devices:
        name = device['name'][:10].ljust(10)  # Обрезаем до 10 символов
        serial = device['serial'].ljust(8)
        room = device['room'][:10].ljust(10)  # Обрезаем до 10 символов
        table_rows.append(f"│ {name} │ {serial} │ {room} │")
    
    table_content = "\n".join(table_rows)
    
    # Создаем кнопки для выбора устройств
    keyboard = []
    for device in devices:
        button_text = f"{device['name']} ({device['serial']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"device_{device['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = table_header + table_content + "\n\n👇 Выберите устройство:"
    await update.message.reply_text(f"```\n{message_text}\n```", 
                                   parse_mode='MarkdownV2', 
                                   reply_markup=reply_markup)

# Обработчик выбора устройства
async def handle_device_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    device_id = int(query.data.split('_')[1])
    # selected_device = next((device for device in devices if device['id'] == device_id), None)
    
#     if selected_device:
#         response = f"""
# 📱 **Информация об устройстве:**
#
# 💻 **Название:** {selected_device['name']}
# 🔢 **Серийный номер:** {selected_device['serial']}
# 🏠 **Комната:** {selected_device['room']}
# 🆔 **ID:** {selected_device['id']}
#
# Что вы хотите сделать с этим устройством?
#         """
#
#         # Кнопки действий для выбранного устройства
#         keyboard = [
#             [InlineKeyboardButton("🔄 Обновить информацию", callback_data=f"edit_{device_id}")],
#             [InlineKeyboardButton("📋 Вернуться к списку", callback_data="back_to_list")],
#             [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{device_id}")]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#
#         await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
#     else:
#         await query.edit_message_text("❌ Устройство не найдено!")

# Обработчик других действий
async def handle_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_list":
        await show_devices_callback(update, context)
    elif query.data.startswith("edit_"):
        device_id = int(query.data.split('_')[1])
        await query.edit_message_text(f"✏️ Редактирование устройства ID: {device_id}\n\nЭта функция в разработке!")
    elif query.data.startswith("delete_"):
        device_id = int(query.data.split('_')[1])
        await query.edit_message_text(f"🗑️ Удаление устройства ID: {device_id}\n\nЭта функция в разработке!")

# Показать устройства через callback (для кнопки "Назад")
async def show_devices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    table_header = "📋 Список ноутбуков:\n\n"
    table_header += "│ Название │ Серийный │ Комната │\n"
    table_header += "├──────────┼──────────┼──────────┤\n"
    
    table_rows = []
    devices = get_devices(DB_PATH)
    for device in devices:
        name = device['name'][:10].ljust(10)
        serial = device['serial'].ljust(8)
        room = device['room'][:10].ljust(10)
        table_rows.append(f"│ {name} │ {serial} │ {room} │")
    
    table_content = "\n".join(table_rows)
    
    keyboard = []
    for device in devices:
        button_text = f"{device['name']} ({device['serial']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"device_{device['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = table_header + table_content + "\n\n👇 Выберите устройство:"
    await query.edit_message_text(f"```\n{message_text}\n```", 
                                 parse_mode='MarkdownV2', 
                                 reply_markup=reply_markup)

# Команда помощи
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
ℹ️ **Помощь по боту:**

Команды:
/start - начать работу
/devices - показать список устройств
/help - эта справка

Как использовать:
1. Нажмите /devices чтобы увидеть таблицу с ноутбуками
2. Выберите устройство из списка кнопок
3. Просмотрите подробную информацию
4. Выполните нужное действие
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


# Основная функция
def main():
    create_db(DB_PATH)
    TOKEN = "7805794447:AAErdCjhBJ1Dxjx3sQgFj0hPXtSKnruvXXI"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("devices", show_devices))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_device_selection, pattern="^device_"))
    application.add_handler(CallbackQueryHandler(handle_actions, pattern="^(back_to_list|edit_|delete_)"))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
