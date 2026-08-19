import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ==================== تنظیمات ====================
BOT_TOKEN = "8616511280:AAERAdaof9H9OmxpYFN0RMfSRmAS5u756wM"
ADMIN_CHAT_ID = "8304841233"  # آیدی ادمین

CARD_NUMBER = "5892-1019-2154-5022"  # شماره کارت
CARD_OWNER = "فاطمه زکی‌زاده"  # صاحب کارت

# ==================== پکیج‌های روباکس ====================
PACKAGES = {
    "400": {"robux": 400, "price": "45,000", "emoji": "💎"},
    "800": {"robux": 800, "price": "85,000", "emoji": "💎💎"},
    "1700": {"robux": 1700, "price": "170,000", "emoji": "👑", "badge": "⭐ پرفروش"},
    "4500": {"robux": 4500, "price": "420,000", "emoji": "🏆"},
    "10000": {"robux": 10000, "price": "900,000", "emoji": "💫", "badge": "🔥 بهترین ارزش"},
}

# ==================== مراحل ====================
CHOOSING_PACKAGE, WAITING_USERNAME, WAITING_RECEIPT = range(3)

# ==================== لاگ ====================
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== دیکشنری سفارشات ====================
orders = {}

# ==================== استارت ====================
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
    keyboard = ReplyKeyboardMarkup(
        [
            ["🛍 خرید روباکس", "📦 پکیج‌ها"],
            ["📋 راهنمای خرید", "📞 پشتیبانی"],
        ],
        resize_keyboard=True
    )
    await update.message.reply_text(text, reply_markup=keyboard)
    return ConversationHandler.END

# ==================== نمایش پکیج‌ها ====================
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

# ==================== انتخاب پکیج ====================
async def package_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.message.reply_text("❌ سفارش لغو شد. هر وقت خواستی دوباره برگرد! 😊")
        return ConversationHandler.END
    pkg_key = query.data.replace("buy_", "")
    pkg = PACKAGES[pkg_key]
    context.user_data["package"] = pkg
    context.user_data["pkg_key"] = pkg_key
    text = (
        f"✅ انتخاب کردی: *{pkg['robux']:,} روباکس* — {pkg['price']} تومان\n\n"
        "👤 حالا *یوزرنیم رابلاکست* رو بفرست:\n"
        "_(مثال: RobloxPlayer123)_"
    )
    await query.message.reply_text(text, parse_mode="Markdown")
    return WAITING_USERNAME

# ==================== دریافت یوزرنیم ====================
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

# ==================== دریافت رسید ====================
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
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأیید و ارسال", callback_data=f"confirm_{order_id}_{user.id}"),
            InlineKeyboardButton("❌ رد کردن", callback_data=f"reject_{order_id}_{user.id}")
        ]
    ])
    try:
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text + "\n⚠️ رسید تصویری ارسال نشد",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error sending to admin: {e}")
    await update.message.reply_text(
        f"✅ *سفارشت ثبت شد!*\n\n"
        f"🆔 شماره سفارش: `{order_id}`\n"
        f"⏳ در حال بررسی توسط پشتیبانی...\n\n"
        "معمولاً تا *۳۰ دقیقه* روباکست ارسال میشه! 🎮",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ==================== تأیید ادمین ====================
async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0]
    order_id = data[1]
    user_id = int(data[2])
    if action == "confirm":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎉 *سفارشت تأیید شد!*\n\n"
                f"🆔 شماره سفارش: `{order_id}`\n"
                "✅ روباکست به زودی به حسابت اضافه میشه!\n\n"
                "ممنون از خریدت! 🎮💎"
            ),
            parse_mode="Markdown"
        )
        await query.message.edit_caption(
            caption=query.message.caption + "\n\n✅ *تأیید شد*",
            parse_mode="Markdown"
        )
    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"❌ *سفارشت تأیید نشد*\n\n"
                f"🆔 شماره سفارش: `{order_id}`\n"
                "⚠️ مشکلی در پرداخت وجود داشت.\n"
                "لطفاً دوباره تلاش کن یا با پشتیبانی تماس بگیر."
            ),
            parse_mode="Markdown"
        )
        await query.message.edit_caption(
            caption=query.message.caption + "\n\n❌ *رد شد*",
            parse_mode="Markdown"
        )

# ==================== راهنما ====================
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

# ==================== پشتیبانی ====================
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📞 *پشتیبانی روباکس شاپ*\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🕐 ساعت کاری: ۹ صبح تا ۱۲ شب\n\n"
        "برای ارتباط با پشتیبانی:\n"
        "👇 پیامت رو همینجا بفرست"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ==================== لغو ====================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# ==================== اجرای ربات ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🛍 خرید روباکس$"), show_packages),
            MessageHandler(filters.Regex("^📦 پکیج‌ها$"), show_packages),
        ],
        states={
            CHOOSING_PACKAGE: [CallbackQueryHandler(package_selected)],
            WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
            WAITING_RECEIPT: [MessageHandler(filters.PHOTO | filters.TEXT, receive_receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_confirm, pattern="^(confirm|reject)_"))
    app.add_handler(MessageHandler(filters.Regex("^📋 راهنمای خرید$"), guide))
    app.add_handler(MessageHandler(filters.Regex("^📞 پشتیبانی$"), support))
    print("✅ ربات روباکس شاپ شروع به کار کرد!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
