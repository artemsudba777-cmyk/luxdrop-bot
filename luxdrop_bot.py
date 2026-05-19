import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")
CHANNEL_URL = "https://t.me/LuxDropReStock"
CHANNEL_ID = "@LuxDropReStock"
SHOP_URL = "https://artemsudba777-cmyk.github.io/luxdrop-bot/luxdrop_shop.html"
OWNER_ID = 6363882470

logging.basicConfig(level=logging.INFO)

PHOTO, NAME, BRAND, PRICE, TYPE, STOCK, SIZES_SELECT = range(7)

ALL_SIZES = ["XS", "S", "M", "L", "XL", "XXL", "3XL"]

def sizes_keyboard(selected):
    buttons = []
    row = []
    for s in ALL_SIZES:
        label = f"✅ {s}" if s in selected else s
        row.append(InlineKeyboardButton(label, callback_data=f"size|{s}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("✅ Готово", callback_data="sizes_done")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Открыть магазин", url=SHOP_URL)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("💬 Связаться с нами", url=f"tg://user?id={OWNER_ID}")],
    ]
    await update.message.reply_text(
        "👋 Добро пожаловать в *LuxDrop | ReStock*!\n\n"
        "🔥 Брендовые вещи по лучшим ценам.\n"
        "📲 Новые поступления каждую неделю.\n"
        "✅ Доставка по всей Украине.\n\n"
        "Выбери что тебя интересует 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def newitem_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text("📸 Отправь фото товара:")
    return PHOTO

async def newitem_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text("✏️ Название товара:")
    return NAME

async def newitem_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("🏷 Бренд:")
    return BRAND

async def newitem_brand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['brand'] = update.message.text
    await update.message.reply_text("💰 Цена (только цифры):")
    return PRICE

async def newitem_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    keyboard = [[
        InlineKeyboardButton("✅ Оригинал", callback_data="type_original"),
        InlineKeyboardButton("🟡 Реплика", callback_data="type_replica")
    ]]
    await update.message.reply_text("🏷 Тип товара:", reply_markup=InlineKeyboardMarkup(keyboard))
    return TYPE

async def newitem_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['type'] = query.data.replace("type_", "")
    type_label = "✅ Оригинал" if context.user_data['type'] == "original" else "🟡 Реплика"
    keyboard = [[
        InlineKeyboardButton("✅ В наличии", callback_data="stock_in"),
        InlineKeyboardButton("❌ Нет в наличии", callback_data="stock_out")
    ]]
    await query.edit_message_text(f"Тип: {type_label}\n\n📦 Наличие:", reply_markup=InlineKeyboardMarkup(keyboard))
    return STOCK

async def newitem_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['instock'] = query.data == "stock_in"
    context.user_data['selected_sizes'] = []
    await query.edit_message_text(
        "📏 Выбери доступные размеры (нажимай чтобы отметить):",
        reply_markup=sizes_keyboard([])
    )
    return SIZES_SELECT

async def newitem_size_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    size = query.data.replace("size|", "")
    selected = context.user_data.get('selected_sizes', [])
    if size in selected:
        selected.remove(size)
    else:
        selected.append(size)
    context.user_data['selected_sizes'] = selected
    await query.edit_message_text(
        "📏 Выбери доступные размеры (нажимай чтобы отметить):",
        reply_markup=sizes_keyboard(selected)
    )
    return SIZES_SELECT

async def newitem_sizes_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sizes = context.user_data.get('selected_sizes', [])
    if not sizes:
        await query.answer("Выбери хотя бы один размер!", show_alert=True)
        return SIZES_SELECT

    data = context.user_data
    type_label = "✅ Оригинал" if data['type'] == "original" else "🟡 Реплика"
    stock_label = "✅ В наличии" if data['instock'] else "❌ Нет в наличии"

    caption = (
        f"🔥 *{data['brand']} — {data['name']}*\n\n"
        f"{type_label} | {stock_label}\n\n"
        f"💰 Цена: *{data['price']} ₴*\n\n"
        f"👇 Выбери размер и закажи:"
    )

    item_key = f"{data['brand']}|{data['name']}|{data['price']}"
    
    # Each size in separate button
    size_buttons = []
    for s in sizes:
        size_buttons.append([InlineKeyboardButton(f"📏 {s}", callback_data=f"order|{item_key}|{s}")])
    size_buttons.append([InlineKeyboardButton("🛍 Все товары", url=SHOP_URL)])

    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=data['photo'],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(size_buttons)
    )

    await query.edit_message_text(
        f"✅ Опубликовано!\n\n*{data['brand']} — {data['name']}*\n{data['price']} ₴\nРазмеры: {', '.join(sizes)}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def handle_order_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Заказ отправлен!", show_alert=True)
    
    parts = query.data.split("|")
    brand = parts[1]
    name = parts[2]
    price = parts[3]
    size = parts[4]
    user = query.from_user

    owner_text = (
        f"🛒 *Новый заказ с канала!*\n\n"
        f"👕 *{brand} — {name}*\n"
        f"📏 Размер: *{size}*\n"
        f"💰 Цена: *{price} ₴*\n\n"
        f"👤 {user.first_name}{' @' + user.username if user.username else ''}\n"
        f"🆔 `{user.id}`"
    )
    keyboard = [[InlineKeyboardButton("💬 Написать покупателю", url=f"tg://user?id={user.id}")]]
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=owner_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"✅ *Заказ принят!*\n\n👕 {brand} — {name}\n📏 Размер: {size}\n💰 {price} ₴\n\nМы свяжемся с вами в ближайшее время 🤝",
            parse_mode="Markdown"
        )
    except:
        pass

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
            f"✅ *Замовлення прийнято!*\n\n{items_text}\n\n💰 *{total}₴*\n\nМи зв'яжемося з вами найближчим часом 🤝",
            parse_mode="Markdown"
        )
        user = update.effective_user
        owner_text = (
            f"🛒 *Новий заказ з магазину!*\n\n"
            f"👤 {user.first_name}{' @' + user.username if user.username else ''}\n"
            f"📞 {phone}\n"
            f"🚚 {delivery}{', ' + city if city else ''}{', №' + branch if branch else ''}\n\n"
            f"{items_text}\n\n💰 *{total}₴*"
        )
        keyboard = [[InlineKeyboardButton("💬 Написати покупцю", url=f"tg://user?id={user.id}")]]
        await context.bot.send_message(chat_id=OWNER_ID, text=owner_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
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
            TYPE: [CallbackQueryHandler(newitem_type, pattern="^type_")],
            STOCK: [CallbackQueryHandler(newitem_stock, pattern="^stock_")],
            SIZES_SELECT: [
                CallbackQueryHandler(newitem_size_toggle, pattern="^size\\|"),
                CallbackQueryHandler(newitem_sizes_done, pattern="^sizes_done$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_order_button, pattern="^order\\|"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    print("✅ LuxDrop бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
