import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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

CHOOSING_PACKAGE, WAITING_USERNAME, WAITING_RECEIPT, SUPPORT_MODE = range(4)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
orders = {}

# ==================== سرور ساده برای Render ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Robux Bot is running!")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()

# ==================== منو ====================
def main_menu():
    return ReplyKeyboardMarkup(
        [["🛍 خرید روباکس", "📦 پکیج‌ها"],
         ["📋 راهنمای خرید", "📞 پشتیبانی"]],
        resize_keyboard=True
    )

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
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return CHOOSING_PACKAGE

async def package_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.message.reply_text("❌ سفارش لغو شد!", reply_markup=main_menu())
        return ConversationHandler.END
    pkg = PACKAGES[query.data.replace("buy_", "")]
    context.user_data["package"] = pkg
    await query.message.reply_text(
        f"✅ انتخاب کردی: *{pkg['robux']:,} روباکس* — {pkg['price']} تومان\n\n"
        "👤 حالا *یوزرنیم رابلاکست* رو بفرست:\n_(مثال: RobloxPlayer123)_",
        parse_mode="Markdown"
    )
    return WAITING_USERNAME

async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["roblox_username"] = update.message.text.strip()
    pkg = context.user_data["package"]
    await update.message.reply_text(
        f"✅ یوزرنیم ثبت شد: *{context.user_data['roblox_username']}*\n\n"
        "━━━━━━━━━━━━━━━\n💳 *اطلاعات پرداخت:*\n"
        f"💰 مبلغ: *{pkg['price']} تومان*\n"
        f"🏦 شماره کارت:\n`{CARD_NUMBER}`\n"
        f"👤 به نام: *{CARD_OWNER}*\n"
        "━━━━━━━━━━━━━━━\n\n📸 عکس رسید رو بفرست!",
        parse_mode="Markdown"
    )
    return WAITING_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pkg = context.user_data["package"]
    roblox_username = context.user_data["roblox_username"]
    order_id = f"ORD{user.id}{len(orders)+1:04d}"
    orders[order_id] = {"user_id": user.id, "package": pkg, "status": "pending"}
    admin_text = (
        f"🔔 *سفارش جدید!*\n━━━━━━━━━━━━━━━\n"
        f"🆔 `{order_id}`\n👤 [{user.first_name}](tg://user?id={user.id})\n"
        f"🎮 یوزرنیم: `{roblox_username}`\n"
        f"💎 {pkg['robux']:,} روباکس\n💰 {pkg['price']} تومان\n━━━━━━━━━━━━━━━"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ تأیید", callback_data=f"confirm_{order_id}_{user.id}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}_{user.id}")
    ]])
    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id,
                caption=admin_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                text=admin_text + "\n⚠️ رسید تصویری نداشت", parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error(e)
    await update.message.reply_text(
        f"✅ *سفارشت ثبت شد!*\n🆔 `{order_id}`\n⏳ تا ۳۰ دقیقه روباکست ارسال میشه! 🎮",
        parse_mode="Markdown", reply_markup=main_menu()
    )
    return ConversationHandler.END

async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    action, order_id, user_id = parts[0], parts[1], int(parts[2])
    if action == "confirm":
        await context.bot.send_message(chat_id=user_id,
            text=f"🎉 *سفارشت تأیید شد!*\n🆔 `{order_id}`\n✅ روباکست اضافه میشه!\nممنون! 🎮💎",
            parse_mode="Markdown")
        try:
            await query.message.edit_caption(caption=query.message.caption + "\n\n✅ تأیید شد", parse_mode="Markdown")
        except:
            pass
    else:
        await context.bot.send_message(chat_id=user_id,
            text=f"❌ *سفارشت تأیید نشد*\n🆔 `{order_id}`\nبا پشتیبانی تماس بگیر.",
            parse_mode="Markdown")
        try:
            await query.message.edit_caption(caption=query.message.caption + "\n\n❌ رد شد", parse_mode="Markdown")
        except:
            pass

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "📞 *پشتیبانی*\n━━━━━━━━━━━━━━━\n\nپیامت رو بنویس 💬\nبرای بازگشت: /start",
        parse_mode="Markdown"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
        text=f"📞 [{user.first_name}](tg://user?id={user.id}) وارد پشتیبانی شد\n🆔 `{user.id}`",
        parse_mode="Markdown")
    return SUPPORT_MODE

async def support_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
        text=f"💬 *پیام جدید پشتیبانی*\n👤 [{user.first_name}](tg://user?id={user.id})\n🆔 `{user.id}`\n📝 {update.message.text}\n\nپاسخ: `/reply {user.id} پیامت`",
        parse_mode="Markdown")
    await update.message.reply_text("✅ پیامت رسید! به زودی جواب میدیم 😊")
    return SUPPORT_MODE

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("فرمت: `/reply آیدی پیام`", parse_mode="Markdown")
        return
    try:
        await context.bot.send_message(chat_id=int(context.args[0]),
            text=f"📩 *پاسخ پشتیبانی:*\n{' '.join(context.args[1:])}", parse_mode="Markdown")
        await update.message.reply_text("✅ پیام ارسال شد!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *راهنمای خرید*\n━━━━━━━━━━━━━━━\n\n"
        "1️⃣ خرید روباکس رو بزن\n2️⃣ پکیج انتخاب کن\n"
        "3️⃣ یوزرنیم رابلاکس بده\n4️⃣ پول واریز کن\n"
        "5️⃣ رسید بفرست\n6️⃣ تا ۳۰ دقیقه روباکس میاد ✅",
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    # سرور رو توی thread جداگانه اجرا کن
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

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
