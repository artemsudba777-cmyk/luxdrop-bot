import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Токен берётся из переменной окружения Railway
TOKEN = os.environ.get("TOKEN")

CHANNEL_URL = "https://t.me/LuxDropReStock"
OWNER_USERNAME = "artemsudba777cmyk"  # замени на свой Telegram username без @

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Перейти в магазин", url=CHANNEL_URL)],
        [InlineKeyboardButton("📦 Новые поступления", callback_data="new")],
        [InlineKeyboardButton("💬 Связаться с нами", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Добро пожаловать в *LuxDrop | ReStock*!\n\n"
        "🔥 Брендовые вещи по лучшим ценам.\n"
        "📲 Новые поступления каждую неделю.\n"
        "✅ Доставка по всей Украине.\n\n"
        "Выбери что тебя интересует 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "new":
        keyboard = [[InlineKeyboardButton("📢 Смотреть новинки", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🆕 *Новые поступления*\n\n"
            "Все свежие дропы публикуем в нашем канале.\n"
            "Подпишись чтобы не пропустить 🔔",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ LuxDrop | ReStock бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
