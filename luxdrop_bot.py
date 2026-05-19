import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

CHANNEL_URL = "https://t.me/LuxDropReStock"
SHOP_URL = "https://artemsudba777-cmyk.github.io/luxdrop-bot/luxdrop_shop.html"
OWNER_USERNAME = "tattoo_on_your_body"
OWNER_ID = 6363882470

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Открыть магазин", url=SHOP_URL)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("💬 Связаться с нами", url=f"https://t.me/{OWNER_USERNAME}")],
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

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        order = data.get("order", [])
        total = data.get("total", 0)

        items_text = "\n".join([f"• {i['brand']} {i['name']} — {i['size']} — {i['price']}₴" for i in order])
        await update.effective_message.reply_text(
            f"✅ *Заказ принят!*\n\n"
            f"{items_text}\n\n"
            f"💰 Итого: *{total}₴*\n\n"
            f"Мы свяжемся с вами в ближайшее время 🤝",
            parse_mode="Markdown"
        )

        user = update.effective_user
        owner_text = (
            f"🛒 *Новый заказ!*\n\n"
            f"👤 Покупатель: {user.first_name}"
            f"{' @' + user.username if user.username else ''}\n"
            f"🆔 ID: `{user.id}`\n\n"
            f"{items_text}\n\n"
            f"💰 Итого: *{total}₴*"
        )
        keyboard = [[InlineKeyboardButton("💬 Написать покупателю", url=f"tg://user?id={user.id}")]]
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=owner_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logging.error(f"Error handling web app data: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    print("✅ LuxDrop | ReStock бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
