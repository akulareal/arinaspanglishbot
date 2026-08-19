from flask import Flask
from threading import Thread

"""
Бот для записи на пробный урок с выбором языка (English / Español).
После выбора языка бот отправляет приветственное сообщение на этом языке,
затем просит контакт и присылает заявку прямо Арине в личку в Telegram.

Как запустить:
1. Установить библиотеку: pip install python-telegram-bot --upgrade
2. Вставить токен бота и chat_id Арины ниже (см. пометки "ВСТАВИТЬ СЮДА")
3. Запустить файл: python bot.py
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
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
ARINA_CHAT_ID = int(os.environ["ARINA_CHAT_ID"])
# ==============================

# Приветственные сообщения на выбранном языке.
# Арина может менять текст здесь вручную.
WELCOME_MESSAGES = {
    "English": "Hey! I’m so happy to see ya 🙌🏼",
    "Español": "Hola! Encantada!🫶",
}

# Состояния диалога
CHOOSING_LANG, ENTERING_CONTACT = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
    ]
    await update.message.reply_text(
        "Привет! На каком языке хочешь пройти пробный урок? / Choose your language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_LANG


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = "English" if query.data == "lang_en" else "Español"
    context.user_data["language"] = lang

    await query.edit_message_text(WELCOME_MESSAGES[lang])

    ask_contact = {
        "English": "Leave your name and phone number (or Telegram username) and I’ll reach out to set up your trial lesson 🙌",
        "Español": "Déjame tu nombre y número de teléfono (o tu usuario de Telegram) y me pondré en contacto para agendar tu clase de prueba 🙌",
    }
    await context.bot.send_message(chat_id=update.effective_chat.id, text=ask_contact[lang])

    return ENTERING_CONTACT


async def enter_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact_info = update.message.text
    lang = context.user_data.get("language")
    user = update.effective_user

    # Отправляем заявку Арине
    notification = (
        f"📩 Новая заявка на пробный урок!\n\n"
        f"Язык: {lang}\n"
        f"Контакт: {contact_info}\n"
        f"Telegram: @{user.username or 'нет юзернейма'}"
    )
    await context.bot.send_message(chat_id=ARINA_CHAT_ID, text=notification)

    thanks = {
        "English": "Thank you! Your request has been sent, Arina will contact you soon 🙌",
        "Español": "¡Gracias! Tu solicitud fue enviada, Arina se pondrá en contacto pronto 🙌",
    }
    await update.message.reply_text(thanks.get(lang, "Спасибо! Заявка отправлена 🙌"))

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запись отменена. Если передумаешь — напиши /start")
    return ConversationHandler.END


web_app = Flask(__name__)


@web_app.route('/')
def home():
    return "Бот жив!"


def run_web():
    web_app.run(host='0.0.0.0', port=10000)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANG: [CallbackQueryHandler(choose_language, pattern="^lang_")],
            ENTERING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен...")
    Thread(target=run_web).start()
    app.run_polling()


if __name__ == "__main__":
    main()
