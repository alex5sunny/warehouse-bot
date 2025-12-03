import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

from db.create_db import create_db
from db.storage import get_devices, set_location, get_device, set_device_name, set_inventory_n
from globs import DB_PATH, SRC_PATH, ADMINS
from logger_config import setup_logger


COL_WIDTH = 6


logger = setup_logger(__file__)


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
    table_header = "📋 Список устройств:\n\n"
    table_header += "│ Назван │ Устрой │ Инвент │ Комнат │ Пользо │\n"
    table_header += "├────────┼────────┼────────┤────────┼────────┤\n"
    
    # Формируем строки таблицы
    table_rows = []
    devices = get_devices(DB_PATH)
    for device in devices:
        name = device['name'][:COL_WIDTH].ljust(COL_WIDTH)
        type = device['type_name'][:COL_WIDTH].ljust(COL_WIDTH)
        inventory_n = device['inventory_n'][:COL_WIDTH].rjust(COL_WIDTH)
        room = device['room'][:COL_WIDTH].ljust(COL_WIDTH)
        user_name = device['user_name'][:COL_WIDTH].ljust(COL_WIDTH)
        table_rows.append(f"│ {name} │ {type} │ {inventory_n} │ {room} │ {user_name} │")
    
    table_content = "\n".join(table_rows)
    
    # Создаем кнопки для выбора устройств
    keyboard = []
    for device in devices:
        button_text = f"{device['name']} ({device['inventory_n']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"device_{device['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = table_header + table_content + "\n\n👇 Выберите устройство:"
    await update.message.reply_text(f"```\n{message_text}\n```", 
                                   parse_mode='MarkdownV2', 
                                   reply_markup=reply_markup)


# Обработчик кнопки "Обновить информацию" - запрашиваем новую локацию
async def handle_update_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[1])
    context.user_data['editing_device_id'] = device_id
    device_name = get_device(DB_PATH, device_id)['name']

    response = f'Введите новую локацию для устройства {device_name}:'
    await query.edit_message_text(response)


async def handle_location_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Проверяем, какое именно редактирование происходит
    if 'editing_name_device_id' in context.user_data:
        device_id = context.user_data['editing_name_device_id']
        set_device_name(DB_PATH, device_id, text)
        context.user_data.pop('editing_name_device_id', None)

    elif 'editing_inventory_device_id' in context.user_data:
        device_id = context.user_data['editing_inventory_device_id']
        set_inventory_n(DB_PATH, device_id, text)
        context.user_data.pop('editing_inventory_device_id', None)

    elif 'editing_device_id' in context.user_data:  # Для локации
        device_id = context.user_data['editing_device_id']
        location = text
        user = update.effective_user
        user_name = user.username if user.username else f"user_{user.id}"
        set_location(DB_PATH, device_id, location, user_name)
        context.user_data.pop('editing_device_id', None)

    # Возвращаем к списку устройств
    await show_devices(update, context)


async def handle_edit_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[2])
    context.user_data['editing_device_id'] = device_id
    device_name = get_device(DB_PATH, device_id)['name']

    response = f"""
✏️ **Редактирование устройства**

💻 **Устройство:** {device_name}

Выберите что изменить:
    """

    # Кнопки выбора действия
    keyboard = [
        [InlineKeyboardButton("📝 Сменить название", callback_data=f"edit_name_{device_id}")],
        [InlineKeyboardButton("🏷️ Сменить инвентарный номер", callback_data=f"edit_inventory_{device_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"device_{device_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)


async def send_location_change_notification(bot, device_before, device_after, changed_by):
    """Отправляет уведомление об изменении локации админам"""

    notification = f"""
🔔 **Изменение локации устройства**

💻 **Устройство:** {device_before['name']}
🔢 **Инвентарный номер:** {device_before['inventory_n']}

📍 **Было:** {device_before['room']}
📍 **Стало:** {device_after['room']}

👤 **Изменено:** {changed_by}
🕐 **Время:** {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
    """

    # Отправляем уведомление всем админам
    for admin_id in ADMINS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=notification,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")


async def handle_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[2])
    context.user_data['editing_name_device_id'] = device_id
    device = get_device(DB_PATH, device_id)

    response = f"""
📝 **Смена названия устройства**

Текущее название: **{device['name']}**

Введите новое название:
    """
    await query.edit_message_text(response, parse_mode='Markdown')

# Обработчик для смены инвентарного номера
async def handle_edit_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[2])
    context.user_data['editing_inventory_device_id'] = device_id
    device = get_device(DB_PATH, device_id)

    response = f"""
🏷️ **Смена инвентарного номера**

Текущий инвентарный: **{device['serial']}**

Введите новый инвентарный номер:
    """
    await query.edit_message_text(response, parse_mode='Markdown')


# Обработчик выбора устройства
async def handle_device_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    device_id = int(query.data.split('_')[1])
    devices = get_devices(DB_PATH)
    selected_device = next((device for device in devices if device['id'] == device_id), None)
    
    if selected_device:
        response = f"""
📱 **Информация об устройстве:**

💻 **Название:** {selected_device['name']}
🔢 **Инвентарный номер:** {selected_device['inventory_n']}
🏠 **Комната:** {selected_device['room']}
🆔 **ID:** {selected_device['id']}

Что вы хотите сделать с этим устройством?
        """

        # Кнопки действий для выбранного устройства
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить локацию", callback_data=f"edit_location_{device_id}")],
            [InlineKeyboardButton("✏️ Редактировать устройство", callback_data=f"edit_device_{device_id}")],
            [InlineKeyboardButton("📋 Вернуться к списку", callback_data="back_to_list")],
            [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{device_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await query.edit_message_text("❌ Устройство не найдено!")


# Обработчик других действий
async def handle_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_list":
        await show_devices_callback(update, context)
    elif query.data.startswith("edit_location_"):
        await handle_update_location(update, context)
    elif query.data.startswith("edit_device_"):
        await handle_edit_device(update, context)
    elif query.data.startswith("edit_name_"):
        await handle_edit_name(update, context)
    elif query.data.startswith("edit_inventory_"):
        await handle_edit_inventory(update, context)
    elif query.data.startswith("delete_"):
        device_id = int(query.data.split('_')[1])
        await query.edit_message_text(f"🗑️ Удаление устройства ID: {device_id}\n\nЭта функция в разработке!")


# Показать устройства через callback (для кнопки "Назад")
async def show_devices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    table_header = "📋 Список устройств:\n\n"
    table_header += "│ Назван │ Устрой │ Серийн │ Комнат  │ Пользо │\n"
    table_header += "├────────┼────────┼────────┤─────────┼────────┤\n"

    table_rows = []
    devices = get_devices(DB_PATH)
    for device in devices:
        name = device['name'][:COL_WIDTH].ljust(COL_WIDTH)
        type = device['type_name'][:COL_WIDTH].ljust(COL_WIDTH)
        inventory_n = device['inventory_n'][:COL_WIDTH].rjust(COL_WIDTH)
        room = device['room'][:COL_WIDTH].ljust(COL_WIDTH)
        user_name = device['user_name'][:COL_WIDTH].ljust(COL_WIDTH)
        table_rows.append(f"│ {name} │ {type} │ {inventory_n} │ {room} │ {user_name} │")
    table_content = "\n".join(table_rows)

    keyboard = []
    for device in devices:
        button_text = f"{device['name']} ({device['inventory_n']})"
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
    create_db(DB_PATH, SRC_PATH / 'sql' / 'create_schema.sql')
    TOKEN = "7805794447:AAErdCjhBJ1Dxjx3sQgFj0hPXtSKnruvXXI"
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("devices", show_devices))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_device_selection, pattern="^device_"))
    application.add_handler(CallbackQueryHandler(
        handle_actions,
        pattern="^(back_to_list|edit_location_|edit_device_|edit_name_|edit_inventory_|delete_)")
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_input))    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
