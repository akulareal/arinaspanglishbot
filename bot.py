from flask import Flask
from threading import Thread

"""
Бот для записи на пробный урок с выбором языка (English / Español).
После выбора языка бот отправляет приветственное сообщение на этом языке
и сразу пересылает заявку Арине в личку в Telegram (со ссылкой на профиль пользователя).

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
    "Español": "Hola! Encantada🫶🏼",
}

# Состояния диалога
CHOOSING_LANG, ENTERING_NAME_AGE = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")],
    ]
    await update.message.reply_text(
        "Привет! На каком языке хочешь пройти пробный урок?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSING_LANG


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = "English" if query.data == "lang_en" else "Español"
    context.user_data["language"] = lang

    await query.edit_message_text(WELCOME_MESSAGES[lang])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Напиши, пожалуйста, свое имя и возраст. Арина свяжется с тобой, чтобы договориться о пробном уроке✍🏻 ",
    )

    return ENTERING_NAME_AGE


async def enter_name_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name_age = update.message.text
    lang = context.user_data.get("language")
    user = update.effective_user

    # Отправляем заявку Арине
    if user.username:
        contact_line = f"https://t.me/{user.username}"
    else:
        contact_line = f'<a href="tg://user?id={user.id}">Открыть чат с пользователем</a>'

    notification = (
        f"📩 Новая заявка на пробный урок!\n\n"
        f"Язык: {lang}\n"
        f"Имя и возраст: {name_age}\n"
        f"Контакт: {contact_line}"
    )
    await context.bot.send_message(
        chat_id=ARINA_CHAT_ID,
        text=notification,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await update.message.reply_text("Спасибо! Заявка отправлена. Ожидай сообщение от Арины 📩")

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
            ENTERING_NAME_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name_age)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Бот запущен...")
    Thread(target=run_web).start()
    app.run_polling()


if __name__ == "__main__":
    main()

