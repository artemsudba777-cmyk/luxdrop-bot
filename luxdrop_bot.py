import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
CHANNEL_URL = "https://t.me/LuxDropReStock"
CHANNEL_ID = "@LuxDropReStock"
SHOP_URL = "https://artemsudba777-cmyk.github.io/luxdrop-bot/luxdrop_shop.html"
OWNER_ID = 6363882470

logging.basicConfig(level=logging.INFO)

# States for adding new item
PHOTO, NAME, BRAND, PRICE, TYPE, STOCK = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Открыть магазин", url=SHOP_URL)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("💬 Связаться с нами", url=f"tg://user?id={OWNER_ID}")],
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

async def newitem_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("📸 Отправь фото товара:")
    return PHOTO

async def newitem_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text("✏️ Название товара (например: Cargo Shorts):")
    return NAME

async def newitem_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("🏷 Бренд (например: Stone Island):")
    return BRAND

async def newitem_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand'] = update.message.text
    await update.message.reply_text("💰 Цена в гривнах (только цифры, например: 5800):")
    return PRICE

async def newitem_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("✅ Оригинал", callback_data="original"),
         InlineKeyboardButton("🟡 Реплика", callback_data="replica")]
    ]
    await update.message.reply_text("🏷 Тип товара:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TYPE

async def newitem_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['type'] = query.data
    type_label = "✅ Оригинал" if query.data == "original" else "🟡 Реплика"
    keyboard = [
        [InlineKeyboardButton("✅ В наличии", callback_data="instock"),
         InlineKeyboardButton("❌ Нет в наличии", callback_data="outstock")]
    ]
    await query.edit_message_text(f"Тип: {type_label}\n\n📦 Наличие:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STOCK

async def newitem_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    in_stock = query.data == "instock"
    context.user_data['instock'] = in_stock

    data = context.user_data
    type_label = "✅ Оригинал" if data['type'] == "original" else "🟡 Реплика"
    stock_label = "✅ В наличии" if in_stock else "❌ Нет в наличии"

    caption = (
        f"🔥 *{data['brand']} — {data['name']}*\n\n"
        f"{type_label}\n"
        f"{stock_label}\n\n"
        f"💰 Цена: *{data['price']} ₴*\n"
        f"📏 Размеры: S / M / L / XL / XXL\n\n"
        f"👇 Заказать в магазине:"
    )

    keyboard = [[InlineKeyboardButton("🛍 Открыть магазин", url=SHOP_URL)]]

    # Post to channel
    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=data['photo'],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await query.edit_message_text(f"✅ Товар опубликован в канале!\n\n{data['brand']} — {data['name']}\n{data['price']} ₴\n{type_label} | {stock_label}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.effective_message.web_app_data.data)
        order = data.get("order", [])
        total = data.get("total", 0)
        name = data.get("name", "")
        phone = data.get("phone", "")
        city = data.get("city", "")
        branch = data.get("branch", "")
        delivery = data.get("delivery", "")

        items_text = "\n".join([f"• {i['brand']} {i['name']} — {i['size']} — {i['price']}₴" for i in order])

        await update.effective_message.reply_text(
            f"✅ *Замовлення прийнято!*\n\n"
            f"{items_text}\n\n"
            f"💰 Підсумок: *{total}₴*\n\n"
            f"Ми зв'яжемося з вами найближчим часом 🤝",
            parse_mode="Markdown"
        )

        user = update.effective_user
        owner_text = (
            f"🛒 *Новий заказ!*\n\n"
            f"👤 {user.first_name}{' @' + user.username if user.username else ''}\n"
            f"📞 {phone}\n"
            f"🚚 {delivery}{', ' + city if city else ''}{', №' + branch if branch else ''}\n\n"
            f"{items_text}\n\n"
            f"💰 Підсумок: *{total}₴*"
        )
        keyboard = [[InlineKeyboardButton("💬 Написати покупцю", url=f"tg://user?id={user.id}")]]
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=owner_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logging.error(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("newitem", newitem_start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, newitem_photo)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, newitem_name)],
            BRAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, newitem_brand)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newitem_price)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, newitem_type),
                   app.callback_query_handler(newitem_type)],
            STOCK: [app.callback_query_handler(newitem_stock)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    print("✅ LuxDrop бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
