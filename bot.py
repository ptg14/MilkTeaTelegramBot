import logging
import uuid
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters, ContextTypes

from config import BOT_TOKEN, OWNER_CHAT_ID, WELCOME_MESSAGE, MENU_FILE, SHOP_NAME
from menu import Menu
from cart import CartManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

menu = Menu(MENU_FILE)
cart_manager = CartManager()

STATE_CATEGORY, STATE_ITEM, STATE_SIZE, STATE_TOPPING, STATE_QTY, STATE_CART, STATE_NAME, STATE_PHONE, STATE_NOTE, STATE_CONFIRM = range(10)


def kb_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧋 Xem Menu", callback_data="menu")],
        [InlineKeyboardButton("🛒 Giỏ Hàng", callback_data="cart")],
        [InlineKeyboardButton("📞 Liên Hệ", callback_data="contact")],
    ])


def kb_category():
    kb = []
    for cat in menu.categories:
        if cat != "Topping":
            emoji = menu.CATEGORY_EMOJI.get(cat, "📋")
            cnt = len(menu.get_available_items(cat))
            kb.append([InlineKeyboardButton(f"{emoji} {cat} ({cnt})", callback_data=f"cat_{cat}")])
    kb.append([InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def kb_items(cat: str):
    items = menu.get_available_items(cat)
    kb = [[InlineKeyboardButton(f"{i.name} - M:{i.price_m//1000}k|L:{i.price_l//1000}k", callback_data=f"item_{i.item_id}")] for i in items]
    kb.append([InlineKeyboardButton("🔙 Quay lại", callback_data="menu")])
    return InlineKeyboardMarkup(kb)


def kb_size(item_id: str):
    item = menu.get_item(item_id)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"M - {item.price_m:,}đ", callback_data=f"size_{item_id}_M"),
         InlineKeyboardButton(f"L - {item.price_l:,}đ", callback_data=f"size_{item_id}_L")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data=f"cat_{item.category}")]
    ])


def kb_topping(selected=None):
    selected = selected or []
    kb = []
    for t in menu.get_toppings():
        check = "✅ " if t.item_id in selected else ""
        kb.append([InlineKeyboardButton(f"{check}{t.name} (+{t.price_m:,}đ)", callback_data=f"top_{t.item_id}")])
    kb.append([InlineKeyboardButton("✅ Xong", callback_data="done_topping"), InlineKeyboardButton("⏭️ Bỏ qua", callback_data="skip_topping")])
    return InlineKeyboardMarkup(kb)


def kb_qty():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(str(i), callback_data=f"qty_{i}") for i in range(1, 4)],
        [InlineKeyboardButton(str(i), callback_data=f"qty_{i}") for i in range(4, 6)] + [InlineKeyboardButton("Khác", callback_data="qty_custom")],
        [InlineKeyboardButton("🔙 Quay lại", callback_data="menu")]
    ])


def kb_cart(empty=False):
    if empty:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🧋 Xem Menu", callback_data="menu")]])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Thêm món", callback_data="menu")],
        [InlineKeyboardButton("🗑️ Xóa món", callback_data="remove_item")],
        [InlineKeyboardButton("🗑️ Xóa hết", callback_data="clear_cart")],
        [InlineKeyboardButton("✅ Đặt hàng", callback_data="checkout")],
        [InlineKeyboardButton("🔙 Menu chính", callback_data="back_main")]
    ])


def kb_confirm():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Xác nhận", callback_data="confirm_order")],
        [InlineKeyboardButton("✏️ Sửa", callback_data="edit_info")],
        [InlineKeyboardButton("🔙 Giỏ hàng", callback_data="cart")]
    ])


def kb_remove(cart):
    kb = [[InlineKeyboardButton(f"❌ {i}. {item.item.name} ({item.size})", callback_data=f"del_{i}")] for i, item in enumerate(cart.items, 1)]
    kb.append([InlineKeyboardButton("🔙 Quay lại", callback_data="cart")])
    return InlineKeyboardMarkup(kb)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode='Markdown', reply_markup=kb_main())
    return STATE_CATEGORY


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txt = """
🆘 *Hướng dẫn*

/start - Bắt đầu
/menu - Xem menu
/cart - Giỏ hàng
/cancel - Hủy

*Cách đặt:*
1. Chọn menu → danh mục → món
2. Chọn size → topping → số lượng
3. Xem giỏ hàng → Đặt hàng
"""
    await update.message.reply_text(txt, parse_mode='Markdown')


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 *Chọn danh mục:*", parse_mode='Markdown', reply_markup=kb_category())
    return STATE_CATEGORY


async def cmd_cart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = cart_manager.get_cart(user.id, user.username or "")
    await update.message.reply_text(cart.format_cart(), parse_mode='Markdown', reply_markup=kb_cart(cart.is_empty))
    return STATE_CART


async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Đã hủy.", reply_markup=kb_main())
    return STATE_CATEGORY


async def cb_main(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "menu":
        await q.edit_message_text("📋 *Chọn danh mục:*", parse_mode='Markdown', reply_markup=kb_category())
        return STATE_CATEGORY
    elif data == "cart":
        user = update.effective_user
        cart = cart_manager.get_cart(user.id, user.username or "")
        await q.edit_message_text(cart.format_cart(), parse_mode='Markdown', reply_markup=kb_cart(cart.is_empty))
        return STATE_CART
    elif data == "contact":
        from config import SHOP_ADDRESS, SHOP_PHONE, WORKING_HOURS
        txt = f"📞 *Liên hệ*\n\n🏪 *{SHOP_NAME}*\n📍 {SHOP_ADDRESS}\n📱 {SHOP_PHONE}\n🕐 {WORKING_HOURS}"
        await q.edit_message_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Quay lại", callback_data="back_main")]]))
        return STATE_CATEGORY
    elif data == "back_main":
        await q.edit_message_text(WELCOME_MESSAGE, parse_mode='Markdown', reply_markup=kb_main())
        return STATE_CATEGORY
    return STATE_CATEGORY


async def cb_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("cat_"):
        cat = q.data[4:]
        ctx.user_data['cat'] = cat
        txt = menu.format_category_menu(cat) + "\n\n👆 Chọn món:"
        await q.edit_message_text(txt, parse_mode='Markdown', reply_markup=kb_items(cat))
        return STATE_ITEM
    return STATE_CATEGORY


async def cb_item(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("item_"):
        item_id = q.data[5:]
        item = menu.get_item(item_id)
        if not item:
            await q.answer("Không tìm thấy!", show_alert=True)
            return STATE_ITEM
        ctx.user_data['item'] = item_id
        txt = f"🧋 *{item.name}*\n\n📝 {item.description}\n\n💰 M: {item.price_m:,}đ | L: {item.price_l:,}đ\n\n👇 Chọn size:"
        await q.edit_message_text(txt, parse_mode='Markdown', reply_markup=kb_size(item_id))
        return STATE_SIZE
    return STATE_ITEM


async def cb_size(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("size_"):
        parts = q.data.split("_")
        item_id, size = parts[1], parts[2]
        ctx.user_data.update({'item': item_id, 'size': size, 'toppings': []})
        item = menu.get_item(item_id)
        await q.edit_message_text(f"🧋 *{item.name}* ({size})\n\n🍡 Thêm topping?", parse_mode='Markdown', reply_markup=kb_topping())
        return STATE_TOPPING
    return STATE_SIZE


async def cb_topping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    selected = ctx.user_data.get('toppings', [])

    if data.startswith("top_"):
        tid = data[4:]
        if tid in selected:
            selected.remove(tid)
        else:
            selected.append(tid)
        ctx.user_data['toppings'] = selected
        await q.answer()

        item = menu.get_item(ctx.user_data['item'])
        size = ctx.user_data['size']
        base = item.get_price(size)
        tp = sum(menu.get_item(t).price_m for t in selected)
        extra = ""
        if selected:
            names = ", ".join(menu.get_item(t).name for t in selected)
            extra = f"\n🍡 Đã chọn: {names}\n💰 Tạm tính: {base + tp:,}đ"
        await q.edit_message_text(f"🧋 *{item.name}* ({size})\n💰 Giá: {base:,}đ{extra}\n\n🍡 Chọn thêm hoặc bấm Xong:", parse_mode='Markdown', reply_markup=kb_topping(selected))
        return STATE_TOPPING

    elif data in ["done_topping", "skip_topping"]:
        await q.answer()
        item = menu.get_item(ctx.user_data['item'])
        size = ctx.user_data['size']
        tp = sum(menu.get_item(t).price_m for t in selected)
        price = item.get_price(size) + tp
        await q.edit_message_text(f"🧋 *{item.name}* ({size})\n💰 Đơn giá: {price:,}đ\n\n📦 Số lượng:", parse_mode='Markdown', reply_markup=kb_qty())
        return STATE_QTY
    return STATE_TOPPING


async def cb_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("qty_"):
        val = q.data[4:]
        if val == "custom":
            await q.edit_message_text("📝 Nhập số lượng (1-99):")
            return STATE_QTY
        return await add_to_cart(update, ctx, int(val))
    return STATE_QTY


async def handle_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text)
        if 1 <= qty <= 99:
            return await add_to_cart(update, ctx, qty, is_msg=True)
        await update.message.reply_text("❌ Số lượng 1-99. Nhập lại:")
        return STATE_QTY
    except:
        await update.message.reply_text("❌ Nhập số hợp lệ:")
        return STATE_QTY


async def add_to_cart(update: Update, ctx: ContextTypes.DEFAULT_TYPE, qty: int, is_msg=False):
    user = update.effective_user
    cart = cart_manager.get_cart(user.id, user.username or "")
    item = menu.get_item(ctx.user_data['item'])
    size = ctx.user_data['size']
    toppings = [menu.get_item(t) for t in ctx.user_data.get('toppings', [])]
    cart.add_item(item, size, qty, toppings)

    tp = sum(t.price_m for t in toppings)
    total = (item.get_price(size) + tp) * qty
    tp_txt = f"\n🍡 {', '.join(t.name for t in toppings)}" if toppings else ""
    txt = f"✅ *Đã thêm!*\n\n🧋 {item.name} ({size}){tp_txt}\n📦 x{qty}\n💰 {total:,}đ\n\n🛒 Giỏ: {cart.total_items} món - {cart.total_price:,}đ"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Thêm món", callback_data="menu")],
        [InlineKeyboardButton("🛒 Giỏ hàng", callback_data="cart")],
        [InlineKeyboardButton("✅ Đặt ngay", callback_data="checkout")]
    ])

    if is_msg:
        await update.message.reply_text(txt, parse_mode='Markdown', reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(txt, parse_mode='Markdown', reply_markup=kb)

    ctx.user_data.pop('item', None)
    ctx.user_data.pop('size', None)
    ctx.user_data.pop('toppings', None)
    return STATE_CATEGORY


async def cb_cart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = update.effective_user
    cart = cart_manager.get_cart(user.id, user.username or "")
    data = q.data

    if data == "remove_item":
        if cart.is_empty:
            await q.answer("Giỏ trống!", show_alert=True)
            return STATE_CART
        await q.edit_message_text("🗑️ *Chọn món xóa:*", parse_mode='Markdown', reply_markup=kb_remove(cart))
        return STATE_CART
    elif data.startswith("del_"):
        idx = int(data[4:])
        cart.remove_item(idx)
        await q.edit_message_text(cart.format_cart(), parse_mode='Markdown', reply_markup=kb_cart(cart.is_empty))
        return STATE_CART
    elif data == "clear_cart":
        cart.clear()
        await q.edit_message_text(cart.format_cart(), parse_mode='Markdown', reply_markup=kb_cart(True))
        return STATE_CART
    elif data == "checkout":
        if cart.is_empty:
            await q.answer("Giỏ trống!", show_alert=True)
            return STATE_CART
        await q.edit_message_text("👤 *Thông tin đặt hàng*\n\nNhập *tên* của bạn:", parse_mode='Markdown')
        return STATE_NAME
    return STATE_CART


async def handle_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = cart_manager.get_cart(user.id)
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❌ Tên quá ngắn:")
        return STATE_NAME
    cart.customer_name = name
    await update.message.reply_text(f"👋 Chào *{name}*!\n\n📱 Nhập *số điện thoại*:", parse_mode='Markdown')
    return STATE_PHONE


async def handle_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = cart_manager.get_cart(user.id)
    phone = update.message.text.strip().replace(" ", "").replace("-", "")
    if not phone.isdigit() or not (9 <= len(phone) <= 11):
        await update.message.reply_text("❌ SĐT không hợp lệ:")
        return STATE_PHONE
    cart.customer_phone = phone
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⏭️ Bỏ qua", callback_data="skip_note")]])
    await update.message.reply_text("📝 Ghi chú (ít đường, ít đá...)?\n\nNhập hoặc bấm Bỏ qua:", reply_markup=kb)
    return STATE_NOTE


async def handle_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = cart_manager.get_cart(user.id)
    cart.delivery_note = update.message.text.strip()
    await update.message.reply_text(cart.format_order_summary(), parse_mode='Markdown', reply_markup=kb_confirm())
    return STATE_CONFIRM


async def cb_skip_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = update.effective_user
    cart = cart_manager.get_cart(user.id)
    await q.edit_message_text(cart.format_order_summary(), parse_mode='Markdown', reply_markup=kb_confirm())
    return STATE_CONFIRM


async def cb_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "confirm_order":
        user = update.effective_user
        cart = cart_manager.get_cart(user.id, user.username or "")
        order_id = f"DH{datetime.now().strftime('%d%m%H%M')}{str(uuid.uuid4())[:4].upper()}"

        notified = True
        try:
            await ctx.bot.send_message(chat_id=OWNER_CHAT_ID, text=cart.format_for_owner(order_id), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Notify failed: {e}")
            notified = False

        txt = f"🎉 *ĐẶT HÀNG THÀNH CÔNG!*\n\n📋 Mã: `{order_id}`\n💵 {cart.total_price:,}đ\n\n✅ Đã gửi đến quán!\n⏳ Vui lòng chờ.\n\nCảm ơn bạn! 🙏"
        if not notified:
            txt += "\n\n⚠️ _Lỗi gửi thông báo. Liên hệ quán để xác nhận._"

        await q.edit_message_text(txt, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧋 Đặt tiếp", callback_data="menu")],
            [InlineKeyboardButton("🏠 Menu", callback_data="back_main")]
        ]))
        cart.clear()
        return STATE_CATEGORY

    elif data == "edit_info":
        await q.edit_message_text("👤 *Sửa thông tin*\n\nNhập lại *tên*:", parse_mode='Markdown')
        return STATE_NAME
    return STATE_CONFIRM


def main():
    if not BOT_TOKEN:
        print("❌ Thiếu BOT_TOKEN trong .env")
        return
    if not OWNER_CHAT_ID:
        print("⚠️ Thiếu OWNER_CHAT_ID - đơn sẽ không gửi được")

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start), CommandHandler("menu", cmd_menu), CommandHandler("cart", cmd_cart)],
        states={
            STATE_CATEGORY: [
                CallbackQueryHandler(cb_main, pattern="^(menu|cart|contact|back_main)$"),
                CallbackQueryHandler(cb_category, pattern="^cat_"),
                CallbackQueryHandler(cb_cart, pattern="^checkout$"),
            ],
            STATE_ITEM: [CallbackQueryHandler(cb_item, pattern="^item_"), CallbackQueryHandler(cb_main, pattern="^menu$")],
            STATE_SIZE: [CallbackQueryHandler(cb_size, pattern="^size_"), CallbackQueryHandler(cb_category, pattern="^cat_")],
            STATE_TOPPING: [CallbackQueryHandler(cb_topping, pattern="^(top_|done_topping|skip_topping)")],
            STATE_QTY: [CallbackQueryHandler(cb_qty, pattern="^qty_"), CallbackQueryHandler(cb_main, pattern="^menu$"), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_qty)],
            STATE_CART: [CallbackQueryHandler(cb_cart, pattern="^(remove_item|del_|clear_cart|checkout)"), CallbackQueryHandler(cb_main, pattern="^(menu|back_main|cart)$")],
            STATE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            STATE_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            STATE_NOTE: [CallbackQueryHandler(cb_skip_note, pattern="^skip_note$"), MessageHandler(filters.TEXT & ~filters.COMMAND, handle_note)],
            STATE_CONFIRM: [CallbackQueryHandler(cb_confirm, pattern="^(confirm_order|edit_info)$"), CallbackQueryHandler(cb_cart, pattern="^cart$")],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel), CommandHandler("start", cmd_start)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", cmd_help))

    print(f"\n🤖 {SHOP_NAME} Bot running...")
    print("Ctrl+C to stop\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
