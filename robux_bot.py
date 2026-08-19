import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ==================== تنظیمات ====================
BOT_TOKEN = "8616511280:AAERAdaof9H9OmxpYFN0RMfSRmAS5u756wM"
ADMIN_CHAT_ID = "8304841233"
CARD_NUMBER = "5892-1019-2154-5022"
CARD_OWNER = "فاطمه زکی‌زاده"

# ==================== پکیج‌های روباکس ====================
PACKAGES = {
    "400": {"robux": 400, "price": "45,000", "emoji": "💎"},
    "800": {"robux": 800, "price": "85,000", "emoji": "💎💎"},
    "1700": {"robux": 1700, "price": "170,000", "emoji": "👑", "badge": "⭐ پرفروش"},
    "4500": {"robux": 4500, "price": "420,000", "emoji": "🏆"},
    "10000": {"robux": 10000, "price": "900,000", "emoji": "💫", "badge": "🔥 بهترین ارزش"},
}

# ==================== مراحل ====================
CHOOSING_PACKAGE, WAITING_USERNAME, WAITING_RECEIPT, SUPPORT_MODE = range(4)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

orders = {}

def main_menu():
    return ReplyKeyboardMarkup(
        [
            ["🛍 خرید روباکس", "📦 پکیج‌ها"],
            ["📋 راهنمای خرید", "📞 پشتیبانی"],
        ],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"سلام {user.first_name} عزیز! 👋\n\n"
        "🎮 به ربات فروش روباکس خوش اومدی!\n"
        "━━━━━━━━━━━━━━━\n"
        "✅ تحویل سریع\n"
        "✅ پشتیبانی ۲۴ ساعته\n"
        "✅ قیمت مناسب\n"
        "━━━━━━━━━━━━━━━\n\n"
        "از منوی پایین یه گزینه انتخاب کن 👇"
    )
    await update.message.reply_text(text, reply_markup=main_menu())
    return ConversationHandler.END

async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💎 پکیج‌های روباکس\n━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    for key, pkg in PACKAGES.items():
        badge = pkg.get("badge", "")
        text += f"{pkg['emoji']} *{pkg['robux']:,} روباکس* — {pkg['price']} تومان {badge}\n"
        keyboard.append([InlineKeyboardButton(
            f"{pkg['emoji']} {pkg['robux']:,} روباکس — {pkg['price']} تومان {badge}",
            callback_data=f"buy_{key}"
        )])
    keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    return CHOOSING_PACKAGE

async def package_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.message.reply_text("❌ سفارش لغو شد. هر وقت خواستی دوباره برگرد! 😊", reply_markup=main_menu())
        return ConversationHandler.END
    pkg_key = query.data.replace("buy_", "")
    pkg = PACKAGES[pkg_key]
    context.user_data["package"] = pkg
    text = (
        f"✅ انتخاب کردی: *{pkg['robux']:,} روباکس* — {pkg['price']} تومان\n\n"
        "👤 حالا *یوزرنیم رابلاکست* رو بفرست:\n"
        "_(مثال: RobloxPlayer123)_"
    )
    await query.message.reply_text(text, parse_mode="Markdown")
    return WAITING_USERNAME

async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()
    context.user_data["roblox_username"] = username
    pkg = context.user_data["package"]
    text = (
        f"✅ یوزرنیم ثبت شد: *{username}*\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💳 *اطلاعات پرداخت:*\n"
        f"💰 مبلغ: *{pkg['price']} تومان*\n"
        f"🏦 شماره کارت:\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 به نام: *{CARD_OWNER}*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "📸 بعد از پرداخت، *عکس رسید* رو اینجا بفرست!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return WAITING_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pkg = context.user_data["package"]
    roblox_username = context.user_data["roblox_username"]
    order_id = f"ORD{user.id}{len(orders)+1:04d}"
    orders[order_id] = {
        "user_id": user.id,
        "username": user.username or user.first_name,
        "roblox_username": roblox_username,
        "package": pkg,
        "status": "pending"
    }
    admin_text = (
        f"🔔 *سفارش جدید!*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🆔 شماره سفارش: `{order_id}`\n"
        f"👤 کاربر: [{user.first_name}](tg://user?id={user.id})\n"
        f"🎮 یوزرنیم رابلاکس: `{roblox_username}`\n"
        f"💎 پکیج: {pkg['robux']:,} روباکس\n"
        f"💰 مبلغ: {pkg['price']} تومان\n"
        f"━━━━━━━━━━━━━━━"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ تأیید و ارسال", callback_data=f"confirm_{order_id}_{user.id}"),
        InlineKeyboardButton("❌ رد کردن", callback_data=f"reject_{order_id}_{user.id}")
    ]])
    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id,
                caption=admin_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                text=admin_text + "\n⚠️ رسید تصویری ارسال نشد", parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error sending to admin: {e}")
    await update.message.reply_text(
        f"✅ *سفارشت ثبت شد!*\n\n🆔 شماره سفارش: `{order_id}`\n⏳ در حال بررسی...\n\nتا *۳۰ دقیقه* روباکست ارسال میشه! 🎮",
        parse_mode="Markdown", reply_markup=main_menu()
    )
    return ConversationHandler.END

async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0]
    order_id = data[1]
    user_id = int(data[2])
    if action == "confirm":
        await context.bot.send_message(chat_id=user_id,
            text=f"🎉 *سفارشت تأیید شد!*\n\n🆔 `{order_id}`\n✅ روباکست به زودی اضافه میشه!\n\nممنون از خریدت! 🎮💎",
            parse_mode="Markdown")
        try:
            await query.message.edit_caption(caption=query.message.caption + "\n\n✅ *تأیید شد*", parse_mode="Markdown")
        except:
            await query.message.edit_text(text=query.message.text + "\n\n✅ *تأیید شد*", parse_mode="Markdown")
    elif action == "reject":
        await context.bot.send_message(chat_id=user_id,
            text=f"❌ *سفارشت تأیید نشد*\n\n🆔 `{order_id}`\n⚠️ مشکلی در پرداخت بود. دوباره تلاش کن یا با پشتیبانی تماس بگیر.",
            parse_mode="Markdown")
        try:
            await query.message.edit_caption(caption=query.message.caption + "\n\n❌ *رد شد*", parse_mode="Markdown")
        except:
            await query.message.edit_text(text=query.message.text + "\n\n❌ *رد شد*", parse_mode="Markdown")

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "📞 *بخش پشتیبانی*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "سوال یا مشکلت رو بنویس — پشتیبانی در اسرع وقت جواب میده! 💬\n\n"
        "برای بازگشت به منو بنویس: /start",
        parse_mode="Markdown"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📞 *کاربر وارد پشتیبانی شد*\n👤 [{user.first_name}](tg://user?id={user.id})\n🆔 آیدی: `{user.id}`",
        parse_mode="Markdown"
    )
    return SUPPORT_MODE

async def support_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    admin_msg = (
        f"💬 *پیام پشتیبانی جدید!*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 کاربر: [{user.first_name}](tg://user?id={user.id})\n"
        f"🆔 آیدی: `{user.id}`\n"
        f"📝 پیام:\n{text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"برای پاسخ: `/reply {user.id} پیامت`"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, parse_mode="Markdown")
    await update.message.reply_text("✅ پیامت دریافت شد!\n⏳ پشتیبانی به زودی جواب میده... 😊")
    return SUPPORT_MODE

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ فرمت درست:\n`/reply آیدی_کاربر پیامت`", parse_mode="Markdown")
        return
    try:
        user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 *پاسخ پشتیبانی:*\n━━━━━━━━━━━━━━━\n{reply_text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ پیام ارسال شد!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *راهنمای خرید روباکس*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "1️⃣ روی *خرید روباکس* بزن\n"
        "2️⃣ پکیج مورد نظرت رو انتخاب کن\n"
        "3️⃣ *یوزرنیم رابلاکست* رو وارد کن\n"
        "4️⃣ مبلغ رو به شماره کارت واریز کن\n"
        "5️⃣ *عکس رسید* رو بفرست\n"
        "6️⃣ منتظر تأیید بمون — تا *۳۰ دقیقه* ✅\n\n"
        "━━━━━━━━━━━━━━━\n"
        "⚠️ *نکات مهم:*\n"
        "• یوزرنیم رابلاکس رو درست وارد کن\n"
        "• رسید واضح باشه\n"
        "• بعد از تأیید روباکس ارسال میشه"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    async def post_init(application):
        await application.bot.delete_webhook(drop_pending_updates=True)

    app.post_init = post_init

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🛍 خرید روباکس$"), show_packages),
            MessageHandler(filters.Regex("^📦 پکیج‌ها$"), show_packages),
            MessageHandler(filters.Regex("^📞 پشتیبانی$"), support_start),
        ],
        states={
            CHOOSING_PACKAGE: [CallbackQueryHandler(package_selected)],
            WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
            WAITING_RECEIPT: [MessageHandler(filters.PHOTO | filters.TEXT, receive_receipt)],
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_confirm, pattern="^(confirm|reject)_"))
    app.add_handler(MessageHandler(filters.Regex("^📋 راهنمای خرید$"), guide))

    print("✅ ربات روباکس شاپ شروع به کار کرد!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
