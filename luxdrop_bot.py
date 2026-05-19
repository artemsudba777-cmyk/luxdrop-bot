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
OWNER_USERNAME = "tattoo_on_your_body"

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

def channel_item_keyboard(item_key):
    """Кнопки в канале — только одна кнопка 'Купить', без размеров"""
    buttons = [
        [InlineKeyboardButton("🛒 Купить", callback_data=f"buy|{item_key}")],
        [InlineKeyboardButton("🛍 Все товары", url=SHOP_URL)],
    ]
    return InlineKeyboardMarkup(buttons)

def personal_sizes_keyboard(item_key, sizes, selected_size=None):
    """Клавиатура с размерами — отправляется в ЛИЧКУ покупателю"""
    buttons = []
    for s in sizes:
        if s == selected_size:
            label = f"✅ {s} — выбран"
        else:
            label = f"📏 {s}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"pick|{item_key}|{s}")])

    if selected_size:
        buttons.append([InlineKeyboardButton(
            f"🛒 Оформить заказ ({selected_size})",
            callback_data=f"order|{item_key}|{selected_size}"
        )])
        buttons.append([InlineKeyboardButton(
            "← Назад к размерам",
            callback_data=f"back|{item_key}|{'~'.join(sizes)}"
        )])

    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛍 Открыть магазин", url=SHOP_URL)],
        [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_URL)],
        [InlineKeyboardButton("💬 Связаться с нами", url=f"https://t.me/{OWNER_USERNAME}")],
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
        "📏 Выбери доступные размеры:",
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
    await query.edit_message_reply_markup(reply_markup=sizes_keyboard(selected))
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
        f"👇 Нажми кнопку чтобы выбрать размер и оформить заказ:"
    )

    # item_key хранит бренд, название, цену и размеры через ~
    sizes_str = "~".join(sizes)
    item_key = f"{data['brand']}|{data['name']}|{data['price']}|{sizes_str}"

    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=data['photo'],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=channel_item_keyboard(item_key)
    )

    await query.edit_message_text(
        f"✅ Опубликовано!\n\n*{data['brand']} — {data['name']}*\n{data['price']} ₴\nРазмеры: {', '.join(sizes)}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def handle_buy_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупатель нажал 'Купить' в канале — отправляем выбор размера в ЛИЧКУ"""
    query = update.callback_query
    await query.answer("Выбери размер в личных сообщениях с ботом 👇")

    parts = query.data.split("|")
    # parts: buy | brand | name | price | sizes_str
    brand = parts[1]
    name = parts[2]
    price = parts[3]
    sizes = parts[4].split("~")
    item_key = f"{brand}|{name}|{price}"

    user = query.from_user

    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"🔥 *{brand} — {name}*\n"
                f"💰 Цена: *{price} ₴*\n\n"
                f"📏 Выбери свой размер:"
            ),
            parse_mode="Markdown",
            reply_markup=personal_sizes_keyboard(item_key, sizes)
        )
    except Exception:
        # Если бот не может написать в личку (пользователь не запускал бота)
        await context.bot.send_message(
            chat_id=user.id,
            text=(
                f"⚠️ Чтобы оформить заказ, сначала нажми /start в боте @LuxDropReStock_bot\n"
                f"Затем вернись и нажми 'Купить' снова."
            )
        )

async def handle_size_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупатель выбрал размер в личке"""
    query = update.callback_query
    await query.answer(f"Размер выбран!")

    parts = query.data.split("|")
    # parts: pick | brand | name | price | size
    brand = parts[1]
    name = parts[2]
    price = parts[3]
    selected_size = parts[4]
    item_key = f"{brand}|{name}|{price}"

    # Получаем список размеров из текущей клавиатуры
    sizes = []
    for row in query.message.reply_markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("pick|"):
                s = btn.callback_data.split("|")[-1]
                sizes.append(s)
            elif btn.callback_data and btn.callback_data.startswith("back|"):
                sizes = btn.callback_data.split("|")[-1].split("~")

    if not sizes:
        sizes = [selected_size]

    await query.edit_message_reply_markup(
        reply_markup=personal_sizes_keyboard(item_key, sizes, selected_size)
    )

async def handle_back_to_sizes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад к выбору размера в личке"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    brand = parts[1]
    name = parts[2]
    price = parts[3]
    sizes = parts[4].split("~")
    item_key = f"{brand}|{name}|{price}"

    await query.edit_message_reply_markup(
        reply_markup=personal_sizes_keyboard(item_key, sizes, None)
    )

async def handle_order_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Покупатель подтвердил заказ в личке"""
    query = update.callback_query
    await query.answer("✅ Заказ оформлен!", show_alert=True)

    parts = query.data.split("|")
    brand, name, price, size = parts[1], parts[2], parts[3], parts[4]
    user = query.from_user

    # Уведомление владельцу
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

    # Подтверждение покупателю
    await query.edit_message_text(
        f"✅ *Заказ принят!*\n\n"
        f"👕 {brand} — {name}\n"
        f"📏 Размер: {size}\n"
        f"💰 {price} ₴\n\n"
        f"Мы свяжемся с вами в ближайшее время 🤝\n\n"
        f"По вопросам: @{OWNER_USERNAME}",
        parse_mode="Markdown"
    )

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
    app.add_handler(CallbackQueryHandler(handle_buy_button, pattern="^buy\\|"))
    app.add_handler(CallbackQueryHandler(handle_size_pick, pattern="^pick\\|"))
    app.add_handler(CallbackQueryHandler(handle_order_button, pattern="^order\\|"))
    app.add_handler(CallbackQueryHandler(handle_back_to_sizes, pattern="^back\\|"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    print("✅ LuxDrop бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
