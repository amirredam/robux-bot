import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8616511280:AAERAdaof9H9OmxpYFN0RMfSRmAS5u756wM"
ADMIN_CHAT_ID = "8304841233"
CARD_NUMBER = "5892-1019-2154-5022"
CARD_OWNER = "فاطمه زکی‌زاده"
REFERRAL_DISCOUNT = 10
WELCOME_GIF = "https://media.giphy.com/media/l4FGrYKtP0pBGpBAU/giphy.gif"

AUTO_REPLIES = {
    "امن": "🔒 *بله کاملاً امنه!*\n\nما هیچوقت رمز یا اطلاعات حسابت رو نمیخوایم.\nفقط یوزرنیم رابلاکست کافیه! ✅",
    "safe": "🔒 *بله کاملاً امنه!*\n\nفقط یوزرنیم رابلاکست کافیه! ✅",
    "خطر": "🔒 *هیچ خطری نداره!*\n\nما روباکس رو از طریق گیفت کارت یا گروپ فاند ارسال میکنیم. اطلاعاتت امنه! ✅",
    "چقدر": "⏱ *معمولاً بین ۵ تا ۳۰ دقیقه!*\n\nبعد از تأیید پرداخت، روباکس ارسال میشه 🚀",
    "چه مدت": "⏱ *معمولاً بین ۵ تا ۳۰ دقیقه!*\n\nبعد از تأیید پرداخت ارسال میشه 🚀",
    "کی میاد": "⏱ *بین ۵ تا ۳۰ دقیقه!*\n\nصبور باش، به زودی میاد 🎮",
    "چه وقت": "⏱ *بین ۵ تا ۳۰ دقیقه!*\n\nبعد از تأیید پرداخت ارسال میشه 🚀",
    "پرداخت": "💳 *روش پرداخت:*\n\nواریز به کارت بانکی\n🏦 `5892-1019-2154-5022`\n👤 فاطمه زکی‌زاده\n\nبعد از واریز عکس رسید بفرست ✅",
    "کارت": "💳 *شماره کارت:*\n\n`5892-1019-2154-5022`\n👤 فاطمه زکی‌زاده\n\nبعد از واریز رسید بفرست! ✅",
    "درگاه": "💳 پرداخت از طریق *کارت بانکی* هست.\n\nشماره کارت:\n`5892-1019-2154-5022`",
    "قیمت": "💎 *قیمت‌های ما:*\n\n💎 400 روباکس — 45,000 تومان\n💎💎 800 روباکس — 85,000 تومان\n👑 1700 روباکس — 170,000 تومان ⭐پرفروش\n🏆 4500 روباکس — 420,000 تومان\n💫 10000 روباکس — 900,000 تومان 🔥\n\nبرای خرید دکمه 🛍 رو بزن!",
    "چند": "💎 *قیمت‌های ما:*\n\n💎 400 روباکس — 45,000 تومان\n👑 1700 روباکس — 170,000 تومان\n💫 10000 روباکس — 900,000 تومان\n\nبرای لیست کامل دکمه 📦 رو بزن!",
    "گرون": "💰 قیمت‌های ما *بهترین قیمت بازار* هستن!\n\nبا کیفیت و تحویل سریع 🚀\nبا کد تخفیف هم میتونی ارزون‌تر بخری 🎁",
    "سلام": "سلام! 👋 *خوش اومدی به Rubax Shop!*\n\nبرای خرید روباکس دکمه 🛍 رو بزن\nسوالی داری؟ اینجام! 😊",
    "هلو": "سلام! 👋 *خوش اومدی!*\n\nبرای خرید دکمه 🛍 رو بزن! 🎮",
    "ممنون": "خواهش میکنم! 😊 همیشه در خدمتیم 🙏",
    "تشکر": "خواهش میکنم! 😊 ممنون که انتخاب کردی! 🙏",
    "یوزرنیم": "👤 *یوزرنیم رابلاکس* همون اسم کاربریته که توی بازی داری.\n\nمثال: RobloxPlayer123\n\n⚠️ مطمئن شو درست وارد میکنی!",
    "آیدی": "👤 *آیدی رابلاکس* همون یوزرنیم بازیته.\n\nمثال: RobloxPlayer123",
    "مشکل": "😔 *ببخشید که مشکل داری!*\n\nشماره سفارشت رو بفرست یا از 📞 پشتیبانی کمک بگیر!",
    "نرسید": "😔 *ببخشید!*\n\nشماره سفارشت رو با `/order شماره` بفرست تا بررسی کنیم! 🔍",
}

PACKAGES = {
    "400": {"robux": 400, "price": 45000, "emoji": "💎"},
    "800": {"robux": 800, "price": 85000, "emoji": "💎💎"},
    "1700": {"robux": 1700, "price": 170000, "emoji": "👑", "badge": "⭐ پرفروش"},
    "4500": {"robux": 4500, "price": 420000, "emoji": "🏆"},
    "10000": {"robux": 10000, "price": 900000, "emoji": "💫", "badge": "🔥 بهترین ارزش"},
}

CHOOSING_PACKAGE, WAITING_USERNAME, WAITING_RECEIPT, SUPPORT_MODE = range(4)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

users = {}
orders = {}
discounts = {}

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Rubax Shop Bot is running!")
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()

def main_menu():
    return ReplyKeyboardMarkup(
        [["🛍 خرید روباکس", "📦 پکیج‌ها"],
         ["📋 راهنمای خرید", "📞 پشتیبانی"],
         ["👤 حساب من", "🎁 دعوت دوستان"]],
        resize_keyboard=True
    )

def register_user(user, ref_id=None):
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.first_name, "username": user.username or "",
            "points": 0, "orders": 0, "total_spent": 0,
            "referrals": 0, "blocked": False,
            "joined": datetime.now().strftime("%Y-%m-%d"), "discount": 0
        }
        if ref_id and str(ref_id) != uid and str(ref_id) in users:
            users[str(ref_id)]["referrals"] += 1
            users[str(ref_id)]["points"] += 50
            users[uid]["discount"] = REFERRAL_DISCOUNT

def is_blocked(user_id):
    return users.get(str(user_id), {}).get("blocked", False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_blocked(user.id):
        await update.message.reply_text("❌ دسترسی شما مسدود شده.")
        return ConversationHandler.END
    ref_id = context.args[0] if context.args else None
    register_user(user, ref_id)
    uid = str(user.id)
    await update.message.reply_animation(
        animation=WELCOME_GIF,
        caption="🎮 *به Rubax Shop خوش اومدی!*\n━━━━━━━━━━━━━━━━━━━\n💎 *بهترین فروشگاه روباکس ایران*\n━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )
    discount_msg = f"\n🎁 *تخفیف {users[uid]['discount']}٪* برای اولین خریدت فعاله!" if users[uid]["discount"] > 0 else ""
    await update.message.reply_text(
        f"سلام *{user.first_name}* عزیز! 👋\n\n"
        "✅ *تحویل فوری ۵ تا ۳۰ دقیقه*\n"
        "✅ *امن و مطمئن ۱۰۰٪*\n"
        "✅ *پشتیبانی ۲۴ ساعته*\n"
        "✅ *بهترین قیمت بازار*\n"
        f"━━━━━━━━━━━━━━━{discount_msg}\n\nاز منوی پایین شروع کن 👇",
        reply_markup=main_menu(), parse_mode="Markdown"
    )
    return ConversationHandler.END

async def smart_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_blocked(update.effective_user.id):
        return
    msg = update.message.text.lower()
    for keyword, reply in AUTO_REPLIES.items():
        if keyword in msg:
            await update.message.reply_text(reply, parse_mode="Markdown")
            return
    await update.message.reply_text(
        "🤔 متوجه نشدم! برای کمک:\n\n"
        "• خرید: دکمه 🛍 رو بزن\n"
        "• سوال: دکمه 📞 پشتیبانی\n"
        "• بازگشت: /start",
        reply_markup=main_menu()
    )

async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_blocked(update.effective_user.id):
        return ConversationHandler.END
    uid = str(update.effective_user.id)
    discount = users.get(uid, {}).get("discount", 0)
    text = "💎 *پکیج‌های روباکس*\n━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    for key, pkg in PACKAGES.items():
        badge = pkg.get("badge", "")
        price = pkg["price"]
        price_text = f"{int(price*(1-discount/100)):,} تومان 🎁{discount}٪" if discount > 0 else f"{price:,} تومان"
        text += f"{pkg['emoji']} *{pkg['robux']:,} روباکس* — {price_text} {badge}\n"
        keyboard.append([InlineKeyboardButton(f"{pkg['emoji']} {pkg['robux']:,} روباکس — {price:,} تومان {badge}", callback_data=f"buy_{key}")])
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
        await query.message.reply_text("❌ لغو شد!", reply_markup=main_menu())
        return ConversationHandler.END
    pkg = PACKAGES[query.data.replace("buy_", "")]
    uid = str(update.effective_user.id)
    discount = users.get(uid, {}).get("discount", 0)
    final_price = int(pkg["price"] * (1 - discount/100)) if discount > 0 else pkg["price"]
    context.user_data["package"] = pkg
    context.user_data["final_price"] = final_price
    context.user_data["discount"] = discount
    await query.message.reply_text(
        f"✅ *{pkg['robux']:,} روباکس*\n💰 *{final_price:,} تومان*"
        + (f" (تخفیف {discount}٪ 🎁)" if discount > 0 else "") +
        "\n\n👤 *یوزرنیم رابلاکست* رو بفرست:\n_(مثال: RobloxPlayer123)_",
        parse_mode="Markdown"
    )
    return WAITING_USERNAME

async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["roblox_username"] = update.message.text.strip()
    final_price = context.user_data["final_price"]
    await update.message.reply_text(
        f"✅ یوزرنیم: *{context.user_data['roblox_username']}*\n\n"
        "━━━━━━━━━━━━━━━\n💳 *اطلاعات پرداخت:*\n"
        f"💰 *{final_price:,} تومان*\n"
        f"🏦 شماره کارت:\n`{CARD_NUMBER}`\n"
        f"👤 *{CARD_OWNER}*\n"
        "━━━━━━━━━━━━━━━\n\n📸 عکس رسید رو بفرست!",
        parse_mode="Markdown"
    )
    return WAITING_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pkg = context.user_data["package"]
    roblox_username = context.user_data["roblox_username"]
    final_price = context.user_data["final_price"]
    discount = context.user_data.get("discount", 0)
    order_id = f"ORD{user.id}{len(orders)+1:04d}"
    orders[order_id] = {"user_id": user.id, "roblox_username": roblox_username, "package": pkg["robux"], "price": final_price, "status": "pending", "date": datetime.now().strftime("%Y-%m-%d %H:%M")}
    uid = str(user.id)
    if uid in users:
        users[uid]["points"] += int(final_price / 1000)
        users[uid]["discount"] = 0
    admin_text = f"🔔 *سفارش جدید!*\n━━━━━━━━━━━━━━━\n🆔 `{order_id}`\n👤 [{user.first_name}](tg://user?id={user.id})\n🎮 `{roblox_username}`\n💎 {pkg['robux']:,} روباکس\n💰 {final_price:,} تومان" + (f" ({discount}٪ تخفیف)" if discount > 0 else "") + "\n━━━━━━━━━━━━━━━"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأیید", callback_data=f"confirm_{order_id}_{user.id}"), InlineKeyboardButton("❌ رد", callback_data=f"reject_{order_id}_{user.id}")]])
    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id, caption=admin_text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text + "\n⚠️ رسید نداشت", parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        logger.error(e)
    await update.message.reply_text(f"✅ *سفارشت ثبت شد!*\n🆔 `{order_id}`\n⏳ تا ۳۰ دقیقه روباکست ارسال میشه! 🎮", parse_mode="Markdown", reply_markup=main_menu())
    return ConversationHandler.END

async def admin_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    action, order_id, user_id = parts[0], parts[1], int(parts[2])
    if action == "confirm":
        uid = str(user_id)
        if uid in users:
            users[uid]["orders"] += 1
            users[uid]["total_spent"] += orders.get(order_id, {}).get("price", 0)
        if order_id in orders:
            orders[order_id]["status"] = "confirmed"
        await context.bot.send_message(chat_id=user_id, text=f"🎉 *تأیید شد!*\n🆔 `{order_id}`\n✅ روباکست اضافه میشه!\nممنون! 🎮💎", parse_mode="Markdown")
        try:
            await query.message.edit_caption(caption=query.message.caption + "\n\n✅ تأیید شد", parse_mode="Markdown")
        except:
            pass
    else:
        if order_id in orders:
            orders[order_id]["status"] = "rejected"
        await context.bot.send_message(chat_id=user_id, text=f"❌ *تأیید نشد*\n🆔 `{order_id}`\nبا پشتیبانی تماس بگیر.", parse_mode="Markdown")
        try:
            await query.message.edit_caption(caption=query.message.caption + "\n\n❌ رد شد", parse_mode="Markdown")
        except:
            pass

async def my_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    u = users[str(user.id)]
    level = "💎 VIP" if u["total_spent"] >= 500000 else "🥈 نقره" if u["total_spent"] >= 200000 else "🥉 برنز"
    text = f"👤 *حساب کاربری*\n━━━━━━━━━━━━━━━\n🏷 *{u['name']}*\n⭐ امتیاز: *{u['points']}*\n📦 سفارشات: *{u['orders']}*\n💰 *{u['total_spent']:,} تومان*\n👥 دعوت‌شدگان: *{u['referrals']}*\n🎖 سطح: *{level}*"
    if u["discount"] > 0:
        text += f"\n🎁 تخفیف: *{u['discount']}٪*"
    await update.message.reply_text(text, parse_mode="Markdown")

async def track_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📦 `/order شماره_سفارش`", parse_mode="Markdown")
        return
    order_id = context.args[0].upper()
    if order_id not in orders:
        await update.message.reply_text("❌ سفارشی پیدا نشد!")
        return
    o = orders[order_id]
    if o["user_id"] != update.effective_user.id and str(update.effective_user.id) != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ این سفارش مال شما نیست!")
        return
    status_map = {"pending": "⏳ در انتظار", "confirmed": "✅ تأیید شده", "rejected": "❌ رد شده"}
    await update.message.reply_text(f"📦 *وضعیت سفارش*\n━━━━━━━━━━━━━━━\n🆔 `{order_id}`\n🎮 `{o['roblox_username']}`\n💎 {o['package']:,} روباکس\n💰 {o['price']:,} تومان\n📅 {o['date']}\nوضعیت: {status_map.get(o['status'], '⏳')}", parse_mode="Markdown")

async def use_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🎁 `/discount کد_تخفیف`", parse_mode="Markdown")
        return
    code = context.args[0].upper()
    uid = str(update.effective_user.id)
    if code not in discounts or discounts[code]["used"] >= discounts[code]["max_use"]:
        await update.message.reply_text("❌ کد تخفیف نامعتبر!")
        return
    register_user(update.effective_user)
    users[uid]["discount"] = discounts[code]["percent"]
    discounts[code]["used"] += 1
    await update.message.reply_text(f"✅ *تخفیف {discounts[code]['percent']}٪ فعال شد!* 🎁", parse_mode="Markdown")

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    uid = str(user.id)
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user.id}"
    u = users[uid]
    await update.message.reply_text(f"🎁 *دعوت دوستان*\n━━━━━━━━━━━━━━━\n\nلینک دعوت:\n`{ref_link}`\n\n👥 دعوت‌شدگان: *{u['referrals']} نفر*\n⭐ امتیاز: *{u['referrals'] * 50}*\n\n🎁 دوستت {REFERRAL_DISCOUNT}٪ تخفیف\nتو ۵۰ امتیاز! 🏆", parse_mode="Markdown")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID or not context.args:
        return
    tid = context.args[0]
    if tid not in users:
        users[tid] = {"name": "ناشناس", "points": 0, "orders": 0, "total_spent": 0, "referrals": 0, "blocked": False, "joined": "", "discount": 0, "username": ""}
    users[tid]["blocked"] = True
    await update.message.reply_text(f"✅ بلاک: `{tid}`", parse_mode="Markdown")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return
    if context.args and context.args[0] in users:
        users[context.args[0]]["blocked"] = False
        await update.message.reply_text("✅ آنبلاک شد!")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID:
        return
    confirmed = sum(1 for o in orders.values() if o["status"] == "confirmed")
    total_income = sum(o["price"] for o in orders.values() if o["status"] == "confirmed")
    await update.message.reply_text(f"📊 *پنل ادمین*\n━━━━━━━━━━━━━━━\n👥 کاربران: *{len(users)}*\n📦 سفارشات: *{len(orders)}*\n✅ تأیید: *{confirmed}*\n💰 درآمد: *{total_income:,} تومان*\n━━━━━━━━━━━━━━━\n• `/addcode کد درصد تعداد`\n• `/block آیدی` | `/unblock آیدی`\n• `/broadcast پیام`\n• `/reply آیدی پیام`", parse_mode="Markdown")

async def add_discount_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID or len(context.args) < 3:
        return
    code, percent, max_use = context.args[0].upper(), int(context.args[1]), int(context.args[2])
    discounts[code] = {"percent": percent, "max_use": max_use, "used": 0}
    await update.message.reply_text(f"✅ کد `{code}` با {percent}٪ ساخته شد!", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID or not context.args:
        return
    msg = " ".join(context.args)
    sent = failed = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *پیام از Rubax Shop:*\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except:
            failed += 1
    await update.message.reply_text(f"✅ موفق: {sent} | ❌ ناموفق: {failed}")

async def support_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    await update.message.reply_text("📞 *پشتیبانی*\n\nپیامت رو بنویس 💬\nبازگشت: /start", parse_mode="Markdown")
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📞 [{user.first_name}](tg://user?id={user.id}) — پشتیبانی\n🆔 `{user.id}`", parse_mode="Markdown")
    return SUPPORT_MODE

async def support_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"💬 *پشتیبانی*\n👤 [{user.first_name}](tg://user?id={user.id})\n🆔 `{user.id}`\n📝 {update.message.text}\n\n`/reply {user.id} پیامت`", parse_mode="Markdown")
    await update.message.reply_text("✅ پیامت رسید! به زودی جواب میدیم 😊")
    return SUPPORT_MODE

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_CHAT_ID or not context.args or len(context.args) < 2:
        return
    try:
        await context.bot.send_message(chat_id=int(context.args[0]), text=f"📩 *پاسخ پشتیبانی:*\n{' '.join(context.args[1:])}", parse_mode="Markdown")
        await update.message.reply_text("✅ ارسال شد!")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 *راهنمای خرید*\n━━━━━━━━━━━━━━━\n\n1️⃣ خرید روباکس\n2️⃣ پکیج انتخاب کن\n3️⃣ یوزرنیم بده\n4️⃣ پول واریز کن\n5️⃣ رسید بفرست\n6️⃣ تا ۳۰ دقیقه روباکس میاد ✅", parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_server, daemon=True).start()
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
    app.add_handler(CommandHandler("order", track_order))
    app.add_handler(CommandHandler("discount", use_discount))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CommandHandler("unblock", unblock_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("addcode", add_discount_code))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_confirm, pattern="^(confirm|reject)_"))
    app.add_handler(MessageHandler(filters.Regex("^📋 راهنمای خرید$"), guide))
    app.add_handler(MessageHandler(filters.Regex("^👤 حساب من$"), my_account))
    app.add_handler(MessageHandler(filters.Regex("^🎁 دعوت دوستان$"), referral))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_reply))

    print("✅ Rubax Shop Bot شروع به کار کرد!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
