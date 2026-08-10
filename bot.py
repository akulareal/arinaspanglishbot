"""
Бот для записи на пробный урок с выбором языка (English / Español).
После записи бот присылает заявку прямо Арине в личку в Telegram.

Как запустить:
1. Установить библиотеку:  pip install python-telegram-bot --upgrade
2. Вставить токен бота и chat_id Арины ниже (см. пометки "ВСТАВИТЬ СЮДА")
3. Запустить файл:  python bot.py
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ==============================
# ВСТАВИТЬ СЮДА: токен от @BotFather
# Пример: "7123456789:AAHf3k2LlksmX9-abcDEFghijklMNOpqrs"
BOT_TOKEN = "СЮДА_ВСТАВИТЬ_ТОКЕН"

# ВСТАВИТЬ СЮДА: chat_id Арины, куда бот будет присылать заявки.
# Как узнать свой chat_id: написать боту @userinfobot, он пришлёт число в ответ.
ARINA_CHAT_ID = 0000000000
# ==============================

# Доступные слоты времени — Арина может менять эти строки вручную
TIME_SLOTS = ["Пн 18:00", "Вт 19:00", "Чт 17:00", "Сб 12:00"]

# Состояния диалога
CHOOSING_LANG, CHOOSING_TIME, ENTERING_CONTACT = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
    ]
    await update.message.reply_text(
        "Привет! На какой язык хочешь записаться на пробный урок?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_LANG


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = "English" if query.data == "lang_en" else "Español"
    context.user_data["language"] = lang

    keyboard = [[InlineKeyboardButton(slot, callback_data=f"time_{slot}")] for slot in TIME_SLOTS]
    await query.edit_message_text(
        f"Отлично, {lang}! Выбери удобное время:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_TIME


async def choose_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_slot = query.data.replace("time_", "")
    context.user_data["time_slot"] = time_slot

    await query.edit_message_text(
        f"Записываю на {time_slot}.\n\nНапиши, пожалуйста, своё имя и телефон (или юзернейм в Telegram), "
        f"чтобы Арина могла с тобой связаться."
    )
    return ENTERING_CONTACT


async def enter_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_info = update.message.text
    lang = context.user_data.get("language")
    time_slot = context.user_data.get("time_slot")
    user = update.effective_user

    # Отправляем заявку Арине
    notification = (
        f"📩 Новая заявка на пробный урок!\n\n"
        f"Язык: {lang}\n"
        f"Время: {time_slot}\n"
        f"Контакт: {contact_info}\n"
        f"Telegram: @{user.username or 'нет юзернейма'}"
    )
    await context.bot.send_message(chat_id=ARINA_CHAT_ID, text=notification)

    await update.message.reply_text(
        "Спасибо! Заявка отправлена, Арина скоро с тобой свяжется 🙌"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена. Если передумаешь — напиши /start")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANG: [CallbackQueryHandler(choose_language, pattern="^lang_")],
            CHOOSING_TIME: [CallbackQueryHandler(choose_time, pattern="^time_")],
            ENTERING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
