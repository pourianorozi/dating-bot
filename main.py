import sqlite3
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# تنظیمات لاگینگ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# مراحل ConversationHandler برای پروفایل
NAME, AGE, GENDER, LOCATION, INTERESTS, BIO, RELATIONSHIP_TYPE = range(7)

# مراحل برای چت
CHAT_MESSAGE = 0

# اتصال به دیتابیس SQLite
def init_db():
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        location TEXT,
        interests TEXT,
        bio TEXT,
        relationship_type TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
        liker_id INTEGER,
        liked_id INTEGER,
        PRIMARY KEY (liker_id, liked_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches (
        user1_id INTEGER,
        user2_id INTEGER,
        PRIMARY KEY (user1_id, user2_id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        user_id INTEGER PRIMARY KEY,
        score INTEGER DEFAULT 0,
        badge TEXT
    )''')
    conn.commit()
    conn.close()

# تابع برای اضافه کردن امتیاز
def add_score(user_id, points):
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO scores (user_id, score) VALUES (?, 0)", (user_id,))
    c.execute("UPDATE scores SET score = score + ? WHERE user_id = ?", (points, user_id))
    c.execute("SELECT score FROM scores WHERE user_id = ?", (user_id,))
    score = c.fetchone()[0]
    badge = "کاربر تازه‌کار" if score < 50 else "کاربر فعال" if score < 200 else "کاربر برتر"
    c.execute("UPDATE scores SET badge = ? WHERE user_id = ?", (badge, user_id))
    conn.commit()
    conn.close()

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("ایجاد پروفایل", callback_data="create_profile")],
        [InlineKeyboardButton("جستجوی کاربران", callback_data="search_users")],
        [InlineKeyboardButton("چت‌های من", callback_data="my_chats")],
        [InlineKeyboardButton("امتیاز من", callback_data="my_score")],
        [InlineKeyboardButton("تنظیمات", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"سلام {user.first_name}! به ربات دوستیابی خوش آمدید! 😊\nلطفاً یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=reply_markup,
    )
    return ConversationHandler.END

# شروع فرآیند ایجاد پروفایل
async def create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("لطفاً نام خود را وارد کنید:")
    return NAME

# ذخیره نام و درخواست سن
async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("لطفاً سن خود را وارد کنید (عدد):")
    return AGE

# ذخیره سن و درخواست جنسیت
async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        age = int(update.message.text)
        if 18 <= age <= 100:
            context.user_data["age"] = age
            keyboard = [
                [InlineKeyboardButton("مرد", callback_data="male")],
                [InlineKeyboardButton("زن", callback_data="female")],
                [InlineKeyboardButton("سایر", callback_data="other")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("لطفاً جنسیت خود را انتخاب کنید:", reply_markup=reply_markup)
            return GENDER
        else:
            await update.message.reply_text("سن باید بین 18 تا 100 باشد. دوباره وارد کنید:")
            return AGE
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد معتبر وارد کنید:")
        return AGE

# ذخیره جنسیت و درخواست مکان
async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    await query.message.reply_text("لطفاً مکان خود را وارد کنید (مثلاً تهران):")
    return LOCATION

# ذخیره مکان و درخواست علایق
async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["location"] = update.message.text
    await update.message.reply_text("علایق خود را وارد کنید (مثلاً موسیقی، ورزش):")
    return INTERESTS

# ذخیره علایق و درخواست بیو
async def interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["interests"] = update.message.text
    await update.message.reply_text("یک توضیح کوتاه درباره خود بنویسید:")
    return BIO

# ذخیره بیو و درخواست نوع رابطه
async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bio"] = update.message.text
    keyboard = [
        [InlineKeyboardButton("دوستی", callback_data="friendship")],
        [InlineKeyboardButton("رابطه جدی", callback_data="serious")],
        [InlineKeyboardButton("گپ‌وگفت معمولی", callback_data="casual")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("نوع رابطه مورد نظر خود را انتخاب کنید:", reply_markup=reply_markup)
    return RELATIONSHIP_TYPE

# ذخیره نوع رابطه و تکمیل پروفایل
async def relationship_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["relationship_type"] = query.data

    # ذخیره در دیتابیس
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO users (user_id, name, age, gender, location, interests, bio, relationship_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            update.effective_user.id,
            context.user_data["name"],
            context.user_data["age"],
            context.user_data["gender"],
            context.user_data["location"],
            context.user_data["interests"],
            context.user_data["bio"],
            context.user_data["relationship_type"],
        ),
    )
    conn.commit()
    conn.close()

    add_score(update.effective_user.id, 50)  # امتیاز برای تکمیل پروفایل

    await query.message.reply_text("پروفایل شما با موفقیت ایجاد شد! 🎉 حالا می‌توانید کاربران را جستجو کنید.")
    return ConversationHandler.END

# جستجوی کاربران
async def search_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id != ?", (update.effective_user.id,))
    users = c.fetchall()
    conn.close()

    if not users:
        await query.message.reply_text("کاربری یافت نشد. بعداً امتحان کنید!")
        return

    user = users[0]  # نمایش اولین کاربر به‌عنوان نمونه
    keyboard = [
        [InlineKeyboardButton("لایک", callback_data=f"like_{user[0]}")],
        [InlineKeyboardButton("رد کردن", callback_data="pass")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        f"نام: {user[1]}\nسن: {user[2]}\nجنسیت: {user[3]}\nمکان: {user[4]}\nعلایق: {user[5]}\nبیو: {user[6]}\nنوع رابطه: {user[7]}",
        reply_markup=reply_markup,
    )

# مدیریت لایک
async def like_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    liked_id = int(query.data.split("_")[1])
    liker_id = update.effective_user.id

    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO likes (liker_id, liked_id) VALUES (?, ?)", (liker_id, liked_id))
    c.execute("SELECT * FROM likes WHERE liker_id = ? AND liked_id = ?", (liked_id, liker_id))
    match = c.fetchone()
    if match:
        c.execute("INSERT OR IGNORE INTO matches (user1_id, user2_id) VALUES (?, ?)", (min(liker_id, liked_id), max(liker_id, liked_id)))
        await query.message.reply_text("تبریک! یک تطبیق (Match) دارید! حالا می‌توانید چت کنید. 🎉")
        await context.bot.send_message(liked_id, "شما یک match جدید دارید! از /chat استفاده کنید.")
    else:
        await query.message.reply_text("لایک شما ثبت شد! در صورت تطبیق، به شما اطلاع می‌دهیم.")
    conn.commit()
    conn.close()
    add_score(liker_id, 10)  # امتیاز برای لایک

# نمایش امتیاز
async def my_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute("SELECT score, badge FROM scores WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        await query.message.reply_text(f"امتیاز شما: {result[0]} ⭐\nبج: {result[1]}")
    else:
        await query.message.reply_text("شما هنوز امتیازی ندارید! فعالیت کنید تا امتیاز بگیرید.")

# شروع چت
async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if len(context.args) != 1:
        await update.message.reply_text("لطفاً user_id را وارد کنید: /chat <user_id>")
        return ConversationHandler.END
    partner_id = int(context.args[0])
    user_id = update.effective_user.id
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM matches WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
              (min(user_id, partner_id), max(user_id, partner_id), min(partner_id, user_id), max(partner_id, user_id)))
    if not c.fetchone():
        await update.message.reply_text("شما با این کاربر match ندارید! ❌")
        return ConversationHandler.END
    conn.close()
    await update.message.reply_text("پیام خود را وارد کنید (برای خروج /cancel):")
    context.user_data["partner_id"] = partner_id
    return CHAT_MESSAGE

# ارسال پیام در چت
async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    partner_id = context.user_data.get("partner_id")
    if not partner_id:
        return ConversationHandler.END
    message = update.message.text
    await context.bot.send_message(partner_id, f"پیام از {update.effective_user.first_name}: {message}")
    await update.message.reply_text("پیام ارسال شد! پیام بعدی را وارد کنید.")
    add_score(update.effective_user.id, 5)  # امتیاز برای ارسال پیام
    return CHAT_MESSAGE

# نمایش چت‌های من
async def my_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    conn = sqlite3.connect("dating_bot.db")
    c = conn.cursor()
    c.execute("SELECT user2_id FROM matches WHERE user1_id = ? UNION SELECT user1_id FROM matches WHERE user2_id = ?", (user_id, user_id))
    matches = c.fetchall()
    conn.close()
    if not matches:
        await query.message.reply_text("شما match ندارید! جستجو کنید.")
        return
    text = "چت‌های شما:\n"
    for match in matches:
        text += f"- کاربر {match[0]}: /chat {match[0]}\n"
    await query.message.reply_text(text)

# مدیریت رد کردن (pass)
async def pass_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("پروفایل رد شد. پروفایل بعدی را جستجو کنید.")

# تنظیمات (خالی برای حالا)
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("تنظیمات: در حال حاضر هیچ تنظیمی موجود نیست. بعداً اضافه می‌شود.")

# لغو فرآیند
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

def main() -> None:
    init_db()
    # دریافت توکن از متغیر محیطی (امن)
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is required. Set it before running the bot.")
    application = Application.builder().token(bot_token).build()

    conv_handler_profile = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_profile, pattern="create_profile")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            GENDER: [CallbackQueryHandler(gender, pattern="^(male|female|other)$")],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, location)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, interests)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
            RELATIONSHIP_TYPE: [CallbackQueryHandler(relationship_type, pattern="^(friendship|serious|casual)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True,
    )

    conv_handler_chat = ConversationHandler(
        entry_points=[CommandHandler("chat", start_chat)],
        states={CHAT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, chat_message)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler_profile)
    application.add_handler(conv_handler_chat)
    application.add_handler(CallbackQueryHandler(search_users, pattern="search_users"))
    application.add_handler(CallbackQueryHandler(like_user, pattern="^like_"))
    application.add_handler(CallbackQueryHandler(pass_user, pattern="pass"))
    application.add_handler(CallbackQueryHandler(my_score, pattern="my_score"))
    application.add_handler(CallbackQueryHandler(my_chats, pattern="my_chats"))
    application.add_handler(CallbackQueryHandler(settings, pattern="settings"))

    application.run_polling()

if __name__ == "__main__":
    main()
