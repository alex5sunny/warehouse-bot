import datetime
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

import main_util.handle_input as handle_input
from db.create_db import create_db
from db.storage import get_devices, get_device, create_device, \
    get_device_types, remove_device
from globs import DB_PATH, SRC_PATH, ADMINS
from logger_config import setup_logger


COL_WIDTH = 6


logger = setup_logger(__file__, level=logging.DEBUG)


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


# Обработчик кнопки "Обновить информацию" - запрашиваем новую локацию
async def handle_update_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[-1])
    context.user_data['editing_device_id'] = device_id
    device_name = get_device(DB_PATH, device_id)['name']

    response = f'Введите новую локацию для устройства {device_name}:'
    await query.edit_message_text(response)


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

Текущий инвентарный: **{device['inventory_n']}**

Введите новый инвентарный номер:
    """
    await query.edit_message_text(response, parse_mode='Markdown')


async def handle_add_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    response = "📝 **Добавление нового устройства**\n\nВыберите тип устройства:"

    keyboard = []
    for type_name in get_device_types(DB_PATH):
        keyboard.append([InlineKeyboardButton(type_name, callback_data=f"type_{type_name}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)

    # Устанавливаем состояние ожидания ввода названия
    context.user_data['adding_device'] = 'type'


async def handle_copy_device(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик копирования устройства"""
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[1])
    device = get_device(DB_PATH, device_id)

    if device:
        # Сохраняем данные копируемого устройства в контексте
        context.user_data['copying_device'] = {
            'device_id': device_id,
            'name': device['name'],
            'type_name': device['type_name'],
            'room': device['room'],
            'user_name': device['user_name']
        }
        context.user_data['adding_device'] = 'copy_inventory'

        response = f"""
📋 **Копирование устройства**

💻 **Устройство:** {device['name']}
🔢 **Тип:** {device['type_name']}

Введите новый инвентарный номер для копии:
        """

        await query.edit_message_text(response, parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ Устройство не найдено!")


async def handle_copy_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение копирования устройства"""
    query = update.callback_query
    await query.answer()

    copying_data = context.user_data.get('copying_device')
    if not copying_data:
        await query.edit_message_text("❌ Данные для копирования не найдены!")
        return

    new_inventory_n = query.data.split('_')[2]

    # Получаем информацию о текущем пользователе из контекста
    user = query.from_user
    user_name = user.username if user.username else f"user_{user.id}"

    # Создаем копию устройства
    create_device(
        DB_PATH,
        copying_data['name'],
        new_inventory_n,
        copying_data['type_name'],
        user_name
    )

    # Очищаем контекст
    context.user_data.pop('copying_device', None)
    context.user_data.pop('adding_device', None)

    # Возвращаем к списку устройств
    await show_devices_callback(update, context)


async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления устройства"""
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[1])
    device = get_device(DB_PATH, device_id)

    if device:
        response = f"""
🗑️ **Удаление устройства**

Вы уверены, что хотите удалить устройство?

💻 **Устройство:** {device['name']}
🔢 **Инвентарный:** {device['inventory_n']}
🏠 **Локация:** {device['room']}

⚠️ **Это действие нельзя отменить!**
        """

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{device_id}"),
                InlineKeyboardButton("❌ Нет, отмена", callback_data=f"device_{device_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await query.edit_message_text("❌ Устройство не найдено!")


async def handle_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Финальное удаление устройства"""
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[2])
    device = get_device(DB_PATH, device_id)

    if device:
        try:
            # Удаляем устройство
            remove_device(DB_PATH, device_id)

            response = f"""
✅ **Устройство удалено**

💻 **Устройство:** {device['name']}
🔢 **Инвентарный:** {device['inventory_n']}

Успешно удалено из базы данных.
            """

            keyboard = [
                [InlineKeyboardButton("📋 К списку устройств", callback_data="back_to_list")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Ошибка при удалении устройства {device_id}: {e}")
            await query.edit_message_text(f"❌ Ошибка при удалении устройства: {e}")
    else:
        await query.edit_message_text("❌ Устройство не найдено!")


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
            [InlineKeyboardButton("📋 Копировать устройство", callback_data=f"copy_{device_id}")],
            [InlineKeyboardButton("📜 История перемещений", callback_data=f"history_{device_id}")],
            [InlineKeyboardButton("📋 Вернуться к списку", callback_data="back_to_list")],
            [InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{device_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await query.edit_message_text("❌ Устройство не найдено!")


async def handle_device_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора типа устройства"""
    query = update.callback_query
    await query.answer()

    # Извлекаем название типа из callback_data
    type_name = query.data[len("type_"):]
    context.user_data['new_device_type'] = type_name
    context.user_data['adding_device'] = 'name'

    response = f"""
📝 **Добавление нового устройства**

Тип: **{type_name}**

Введите название устройства:
    """

    await query.edit_message_text(response, parse_mode='Markdown')


async def handle_device_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает историю перемещений устройства"""
    query = update.callback_query
    await query.answer()

    device_id = int(query.data.split('_')[1])
    device = get_device(DB_PATH, device_id)

    if not device:
        await query.edit_message_text("❌ Устройство не найдено!")
        return

    # Получаем историю
    from db.storage import get_device_history
    history_records = get_device_history(DB_PATH, device_id, limit=15)

    if not history_records:
        response = f"""
📜 **История перемещений**

💻 **Устройство:** {device['name']}
🔢 **Инвентарный:** {device['inventory_n']}

История перемещений отсутствует.
        """

        keyboard = [
            [InlineKeyboardButton("🔙 Назад к устройству", callback_data=f"device_{device_id}")],
            [InlineKeyboardButton("📋 К списку устройств", callback_data="back_to_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
        return

    # Формируем сообщение с историей
    response = f"""
📜 **История перемещений**

💻 **Устройство:** {device['name']}
🔢 **Инвентарный:** {device['inventory_n']}

Последние перемещения:
────────────────────
"""

    # Добавляем записи истории
    for i, record in enumerate(history_records, 1):
        # Форматируем дату для читаемости
        date_str = record['date_time']
        # Если дата в формате SQLite (YYYY-MM-DD HH:MM:SS)
        if len(date_str) > 10:
            # Преобразуем в более читаемый формат
            try:
                dt = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                date_formatted = dt.strftime('%d.%m.%Y %H:%M')
            except:
                date_formatted = date_str
        else:
            date_formatted = date_str

        room = record['room'] or "Не указана"
        user_name = record['user_name'] or "Не указан"

        response += f"\n{i}. **{date_formatted}**\n"
        response += f"   📍 **Локация:** {room}\n"
        response += f"   👤 **Пользователь:** {user_name}\n"
        response += "   ────────────────"

    response += f"\n\nВсего записей: {len(history_records)}"

    # Кнопки для навигации
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить локацию", callback_data=f"edit_location_{device_id}")],
        [InlineKeyboardButton("🔙 Назад к устройству", callback_data=f"device_{device_id}")],
        [InlineKeyboardButton("📋 К списку устройств", callback_data="back_to_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)


# Обработчик других действий
async def handle_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("copy_"):
        await handle_copy_device(update, context)
    elif query.data.startswith("confirm_copy_"):
        await handle_copy_complete(update, context)
    elif query.data.startswith("history_"):
        await handle_device_history(update, context)
    elif query.data == "back_to_list":
        await show_devices_callback(update, context)
    elif query.data == "add_device":
        await handle_add_device(update, context)
    elif query.data.startswith("type_"):
        await handle_device_type_selection(update, context)
    elif query.data.startswith("edit_location_"):
        await handle_update_location(update, context)
    elif query.data.startswith("edit_device_"):
        await handle_edit_device(update, context)
    elif query.data.startswith("edit_name_"):
        await handle_edit_name(update, context)
    elif query.data.startswith("edit_inventory_"):
        await handle_edit_inventory(update, context)
    elif query.data.startswith("delete_"):
        await handle_delete_confirmation(update, context)  # Теперь запрашиваем подтверждение
    elif query.data.startswith("confirm_delete_"):
        await handle_confirm_delete(update, context)


def get_devices_table_and_keyboard():
    """Возвращает таблицу устройств и клавиатуру для нее"""
    devices = get_devices(DB_PATH)

    # Создаем таблицу
    table_header = "📋 Список устройств:\n\n"
    table_header += "│ Назван │ Устрой │ Инвент │ Комнат │ Пользо │\n"
    table_header += "├────────┼────────┼────────┤────────┼────────┤\n"

    table_rows = []
    for device in devices:
        name = device['name'][:COL_WIDTH].ljust(COL_WIDTH)
        type = device['type_name'][:COL_WIDTH].ljust(COL_WIDTH)
        inventory_n = device['inventory_n'][:COL_WIDTH].rjust(COL_WIDTH)
        room = device['room'][:COL_WIDTH].ljust(COL_WIDTH)
        user_name = device['user_name'][:COL_WIDTH].ljust(COL_WIDTH)
        table_rows.append(f"│ {name} │ {type} │ {inventory_n} │ {room} │ {user_name} │")

    table_content = "\n".join(table_rows)
    message_text = table_header + table_content + "\n\n👇 Выберите устройство или добавьте новое:"

    # Создаем клавиатуру
    keyboard = []
    for device in devices:
        button_text = f"{device['name']} ({device['inventory_n']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"device_{device['id']}")])

    keyboard.append([InlineKeyboardButton("➕ Добавить устройство", callback_data="add_device")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    return f"```\n{message_text}\n```", reply_markup


# Команда /devices - показывает таблицу с кнопками
async def show_devices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text, reply_markup = get_devices_table_and_keyboard()
    await update.message.reply_text(message_text,
                                    parse_mode='MarkdownV2',
                                    reply_markup=reply_markup)


# Показать устройства через callback (для кнопки "Назад")
async def show_devices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    message_text, reply_markup = get_devices_table_and_keyboard()
    await query.edit_message_text(message_text,
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
    application.add_handler(
        CallbackQueryHandler(handle_device_selection, pattern="^device_")
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_actions,
            pattern="^(copy_|confirm_copy_|back_to_list|add_device|"
                    "type_|edit_location_|edit_device_|edit_name_|"
                    "edit_inventory_|delete_|confirm_delete_|history_)"
        )
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input.handle_input)
    )

    print("Бот запущен...")
    while True:
        try:
            application.run_polling()
        except:
            logger.exception('restart after exception..')


if __name__ == '__main__':
    main()
