from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db.storage import create_device, set_device_name, set_inventory_n, get_device, set_location, insert_history_record
from globs import DB_PATH
from main import show_devices, send_location_change_notification


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if context.user_data.get('adding_device') == 'copy_inventory':
        # Пользователь ввел инвентарный номер для копии
        copying_data = context.user_data.get('copying_device')
        if not copying_data:
            await update.message.reply_text("❌ Ошибка: данные для копирования не найдены!")
            return

        # Получаем информацию о текущем пользователе
        user = update.effective_user
        user_name = user.username if user.username else f"user_{user.id}"

        response = f"""
📋 **Подтверждение копирования**

💻 **Устройство:** {copying_data['name']}
🔢 **Тип:** {copying_data['type_name']}
🏷️ **Новый инвентарный:** {text}
👤 **Пользователь:** {user_name}

Подтвердите создание копии:
    """

        keyboard = [
            [
                InlineKeyboardButton("✅ Создать копию", callback_data=f"confirm_copy_{text}"),
                InlineKeyboardButton("❌ Отмена", callback_data=f"device_{copying_data['device_id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)

        context.user_data['pending_inventory'] = text
        return
    elif context.user_data.get('adding_device') == 'name':
        # Сохраняем название и запрашиваем инвентарный номер
        context.user_data['new_device_name'] = text
        context.user_data['adding_device'] = 'inventory'

        response = f"""
📝 **Добавление нового устройства**

Тип: **{context.user_data['new_device_type']}**
Название: **{text}**

Теперь введите инвентарный номер:
            """
        await update.message.reply_text(response, parse_mode='Markdown')
        return

    elif context.user_data.get('adding_device') == 'inventory':
        # Создаем устройство с сохраненным названием и введенным инвентарным номером
        name = context.user_data['new_device_name']
        inventory_n = text
        device_type = context.user_data['new_device_type']

        user = update.effective_user
        user_name = user.username if user.username else f"user_{user.id}"

        # Создаем устройство в БД
        create_device(DB_PATH, name, inventory_n, device_type, user_name)

        # Очищаем контекст
        context.user_data.pop('adding_device', None)
        context.user_data.pop('new_device_type', None)
        context.user_data.pop('new_device_name', None)

        # Возвращаем к списку устройств
        await show_devices(update, context)
        return
    elif 'editing_name_device_id' in context.user_data:
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

        device_before = get_device(DB_PATH, device_id)
        set_location(DB_PATH, device_id, location, user_name)
        device_after = get_device(DB_PATH, device_id)

        insert_history_record(DB_PATH, device_id)

        await send_location_change_notification(
            context.bot,
            device_before,
            device_after,
            user_name
        )

        context.user_data.pop('editing_device_id', None)

    # Возвращаем к списку устройств
    await show_devices(update, context)
