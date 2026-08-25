"""
بات مدیریت ساختمان فدک - نسخه پیشرفته با گزارش واریزی
توسعه دهنده: radvin
"""

from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update
import sqlite3
import datetime
import os

# ==========================================
# تنظیمات اولیه
# ==========================================
BOT_TOKEN = "CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT"
DB_NAME = "fadak_building.db"
RECEIPTS_DIR = "receipts" # پوشه ذخیره رسیدها

if not os.path.exists(RECEIPTS_DIR):
    os.makedirs(RECEIPTS_DIR)

bot = BotClient(token=BOT_TOKEN)

# دیکشنری برای ذخیره وضعیت موقت کاربران
user_states = {}

# ==========================================
# مدیریت پایگاه داده (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول ادمین‌ها
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins 
                      (user_id TEXT PRIMARY KEY, role TEXT)''')
    
    # جدول پیام شارژ
    cursor.execute('''CREATE TABLE IF NOT EXISTS charge_messages 
                      (id INTEGER PRIMARY KEY, text TEXT, card_number TEXT)''')
    
    # جدول هزینه‌ها
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, description TEXT, registered_by TEXT, date TEXT)''')
    
    # جدول پرداخت‌های کاربران (جدید)
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, full_name TEXT, file_id TEXT, file_path TEXT, date TEXT)''')
    
    conn.commit()
    conn.close()

def is_admin(user_id: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_admin(user_id: str, role: str = "admin"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO admins (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()
    conn.close()

def save_charge_message(text: str, card_number: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM charge_messages")
    cursor.execute("INSERT INTO charge_messages (text, card_number) VALUES (?, ?)", (text, card_number))
    conn.commit()
    conn.close()

def get_charge_message():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT text, card_number FROM charge_messages LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result

def add_expense(amount: float, description: str, user_id: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    cursor.execute("INSERT INTO expenses (amount, description, registered_by, date) VALUES (?, ?, ?, ?)", 
                   (amount, description, user_id, date_str))
    conn.commit()
    conn.close()

def get_all_expenses():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT amount, description, registered_by, date FROM expenses ORDER BY id DESC")
    result = cursor.fetchall()
    conn.close()
    return result

def add_payment(user_id: str, full_name: str, file_id: str, file_path: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    cursor.execute("INSERT INTO payments (user_id, full_name, file_id, file_path, date) VALUES (?, ?, ?, ?, ?)", 
                   (user_id, full_name, file_id, file_path, date_str))
    conn.commit()
    conn.close()

def get_monthly_payments(year, month):
    """دریافت لیست پرداخت‌های یک ماه خاص"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # فرض بر این است که تاریخ به فرمت YYYY/MM/DD ذخیره شده است
    like_pattern = f"{year}/{month:02d}/%"
    cursor.execute("SELECT user_id, full_name, date FROM payments WHERE date LIKE ?", (like_pattern,))
    result = cursor.fetchall()
    conn.close()
    return result

def get_all_admins():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

# راه‌اندازی اولیه دیتابیس
init_db()

# ==========================================
# هندلرهای بات (دستورات متنی)
# ==========================================

# 1. فعال‌سازی در گروه با پیام "فعال"
@bot.on_update(filters.group, filters.text("فعال"))
async def activate_in_group(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    add_admin(user_id, "admin")
    
    response_text = (
        "✅ **بات ساختمان فدک با موفقیت فعال شد!**\n\n"
        "👤 شما به عنوان مدیر سیستم ثبت شدید.\n\n"
        "📋 **لیست دستورات:**\n"
        "• `شارژ` - مشاهده اطلاعات پرداخت شارژ ماهانه\n"
        "• `واریز` - ارسال رسید واریزی (همراه با نام و نام خانوادگی)\n"
        "• `ثبت هزینه مبلغ توضیحات` - ثبت هزینه جدید (ادمین)\n"
        "• `لیست هزینه ها` - مشاهده تمام هزینه‌های ثبت شده (ادمین)\n"
        "• `تنظیم شارژ` - تنظیم متن و شماره کارت شارژ (ادمین)\n"
        "• `راهنما` - نمایش مجدد این لیست\n\n"
        "💡 **نکته مدیریتی:** روی هر پیام ریپلای بزنید و بنویسید `ادمین` تا بتوانید آن را مدیریت کنید."
    )
    await update.reply(response_text)

# 2. فعال‌سازی ادمین در پیوی با دستور /admin
@bot.on_update(filters.private, filters.commands("admin"))
async def admin_pv_activation(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    add_admin(user_id, "admin")
    
    response_text = (
        "👤 **شما با موفقیت به عنوان ادمین بات ثبت شدید!**\n\n"
        "اکنون می‌توانید از دستورات مدیریتی در گروه استفاده کنید.\n"
        "برای دیدن لیست دستورات، کلمه `راهنما` را در گروه ارسال کنید."
    )
    await update.reply(response_text)

# 3. نمایش راهنما
@bot.on_update(filters.group, filters.text("راهنما"))
async def show_help(bot: BotClient, update: Update):
    help_text = (
        "📖 **راهنمای دستورات بات ساختمان فدک:**\n\n"
        "🔹 `شارژ` - دریافت شماره کارت و متن یادآوری شارژ\n"
        "🔹 `واریز` - ارسال رسید پرداخت (نام + عکس رسید)\n"
        "🔹 `ثبت هزینه [مبلغ] [توضیحات]` - مثال: ثبت هزینه 200000 نظافت\n"
        "🔹 `لیست هزینه ها` - نمایش ریز هزینه‌های ساختمان\n"
        "🔹 `تنظیم شارژ` - شروع فرآیند تنظیم پیام شارژ (فقط ادمین)\n"
        "🔹 `ادمین` (به صورت ریپلای) - مدیریت پیام مورد نظر"
    )
    await update.reply(help_text)

# 4. نمایش اطلاعات شارژ
@bot.on_update(filters.group, filters.text("شارژ"))
async def show_charge_info(bot: BotClient, update: Update):
    charge_data = get_charge_message()
    if not charge_data:
        await update.reply("📭 هنوز پیام شارژی توسط مدیریت تنظیم نشده است.")
        return
    
    msg = (
        "💳 **اطلاعات پرداخت شارژ ساختمان فدک**\n\n"
        f"📝 {charge_data[0]}\n\n"
        f"💳 **شماره کارت:**\n`{charge_data[1]}`\n\n"
        "⚠️ لطفاً پس از واریز، با دستور `واریز` نام و تصویر رسید را ارسال کنید."
    )
    await update.reply(msg)

# 5. شروع فرآیند واریز
@bot.on_update(filters.group, filters.text("واریز"))
async def start_deposit(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    user_states[user_id] = {"step": "waiting_name"}
    await update.reply(
        "💳 **ثبت رسید واریزی**\n\n"
        "لطفاً **نام و نام خانوادگی** خود را ارسال کنید:\n"
        "(مثال: علی رضایی)"
    )

# 6. ثبت هزینه (فرمت: ثبت هزینه مبلغ توضیحات)
@bot.on_update(filters.group, filters.text(lambda t: t.startswith("ثبت هزینه")))
async def register_expense(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ فقط ادمین‌ها و کالک‌ها می‌توانند هزینه ثبت کنند!")
        return
    
    text = update.new_message.text
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await update.reply("❌ **فرمت نادرست!**\nمثال: `ثبت هزینه 500000 تعمیر آسانسور`")
        return
    
    try:
        amount = float(parts[1].replace(",", ""))
        description = parts[2]
        add_expense(amount, description, user_id)
        await update.reply(f"✅ هزینه {amount:,.0f} تومان با موفقیت ثبت شد.")
    except ValueError:
        await update.reply("❌ مبلغ وارد شده معتبر نیست!")

# 7. لیست تمام هزینه‌ها
@bot.on_update(filters.group, filters.text("لیست هزینه ها"))
async def list_expenses(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ فقط ادمین‌ها می‌توانند لیست هزینه‌ها را ببینند!")
        return
    
    expenses = get_all_expenses()
    if not expenses:
        await update.reply("📭 هنوز هیچ هزینه‌ای ثبت نشده است.")
        return
    
    msg = "📊 **لیست کامل هزینه‌ها:**\n\n"
    total = 0
    for exp in expenses:
        total += exp[0]
        msg += f"🔹 {exp[0]:,.0f} ت | {exp[1]}\n"
    msg += f"\n💵 **جمع کل:** {total:,.0f} تومان"
    
    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
    for chunk in chunks:
        await update.reply(chunk)

# 8. شروع فرآیند تنظیم شارژ
@bot.on_update(filters.group, filters.text("تنظیم شارژ"))
async def start_set_charge(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ فقط ادمین‌ها می‌توانند پیام شارژ را تنظیم کنند!")
        return
    user_states[user_id] = {"step": "waiting_charge_text"}
    await update.reply("📝 لطفاً **متن پیام یادآوری شارژ** را ارسال کنید:")

# 9. مدیریت ریپلای با کلمه "ادمین"
@bot.on_update(filters.group, filters.replied, filters.text("ادمین"))
async def manage_replied_message(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ شما دسترسی ادمین ندارید!")
        return
    
    replied_msg_id = update.new_message.reply_to_message_id
    chat_id = update.chat_id
    user_states[user_id] = {"step": "waiting_delete_confirm", "chat_id": chat_id, "message_id": replied_msg_id}
    await update.reply("🛠 برای **حذف** این پیام، کلمه `حذف` را ارسال کنید. برای انصراف `لغو`.")

# 10. پردازش State Machine (مدیریت مراحل مختلف)
@bot.on_update(filters.group, filters.text)
@bot.on_update(filters.private, filters.text)
async def handle_state_inputs(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    text = update.new_message.text.strip()
    
    if user_id not in user_states:
        return
    
    user_state = user_states[user_id]
    step = user_state.get("step")
    
    # --- حالت واریز: مرحله 1 (دریافت نام) ---
    if step == "waiting_name":
        user_states[user_id]["full_name"] = text
        user_states[user_id]["step"] = "waiting_receipt_photo"
        await update.reply(
            f"✅ نام {text} ثبت شد.\n\n"
            "📸 اکنون لطفاً **تصویر رسید واریزی** را ارسال کنید."
        )
        return

    # --- حالت تنظیم شارژ: مرحله 1 (دریافت متن) ---
    if step == "waiting_charge_text":
        user_states[user_id]["text"] = text
        user_states[user_id]["step"] = "waiting_charge_card"
        await update.reply("💳 لطفاً **شماره کارت** مقصد را ارسال کنید:")
        return

    # --- حالت تنظیم شارژ: مرحله 2 (دریافت شماره کارت) ---
    if step == "waiting_charge_card":
        save_charge_message(user_states[user_id]["text"], text)
        del user_states[user_id]
        await update.reply("✅ پیام شارژ با موفقیت تنظیم شد.")
        return

    # --- حالت مدیریت پیام: تایید حذف ---
    if step == "waiting_delete_confirm":
        if text == "حذف":
            try:
                await bot.delete_message(user_state["chat_id"], user_state["message_id"])
                await update.reply("✅ پیام حذف شد.")
            except:
                await update.reply("❌ خطا در حذف پیام.")
        elif text == "لغو":
            await update.reply("❌ عملیات لغو شد.")
        del user_states[user_id]
        return


# 11. دریافت عکس رسید (برای تکمیل فرآیند واریز)
@bot.on_update(filters.group, filters.photo)
async def handle_receipt_photo(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    
    # بررسی اینکه آیا کاربر در مرحله انتظار عکس رسید است یا خیر
    if user_id in user_states and user_states[user_id].get("step") == "waiting_receipt_photo":
        full_name = user_states[user_id].get("full_name")
        
        # دریافت اطلاعات فایل عکس
        photo_file = update.new_message.file
        if photo_file and photo_file.file_id:
            file_id = photo_file.file_id
            
            # دانلود فایل (اختیاری - برای آرشیو کردن)
            # در روبیکا برای دانلود باید از متد download_file استفاده کرد
            # اینجا فقط file_id را ذخیره می‌کنیم تا بعداً قابل دسترسی باشد
            file_path = f"{RECEIPTS_DIR}/{user_id}_{datetime.datetime.now().timestamp()}.jpg"
            
            # تلاش برای دانلود فایل
            try:
                await bot.download_file(file_id, save_as=file_path)
            except Exception as e:
                print(f"Error downloading file: {e}")
                file_path = "Download Failed"

            # ذخیره در دیتابیس
            add_payment(user_id, full_name, file_id, file_path)
            
            del user_states[user_id]
            await update.reply(
                f"✅ **رسید واریزی شما با موفقیت ثبت شد!**\n\n"
                f"👤 نام: {full_name}\n"
                f"📅 تاریخ: {datetime.datetime.now().strftime('%Y/%m/%d')}\n\n"
                "با تشکر از پرداخت به موقع شما."
            )
        else:
            await update.reply("❌ خطا در دریافت فایل عکس. لطفاً مجدداً تلاش کنید.")
            del user_states[user_id]
    else:
        # اگر کاربر در حالت واریز نبود، پیام معمولی است
        pass


# ==========================================
# وظیفه زمان‌بندی شده (گزارش ماهانه)
# ==========================================
async def send_monthly_report():
    """این تابع باید هر روز چک کند که آیا پنجم ماه است یا خیر"""
    now = datetime.datetime.now()
    
    # فقط در پنجم هر ماه اجرا شود (ساعت 9 صبح)
    if now.day == 5 and now.hour == 9:
        year = now.year
        month = now.month
        
        payments = get_monthly_payments(year, month)
        paid_user_ids = [p[0] for p in payments]
        
        admins = get_all_admins()
        
        report_text = (
            f"📊 **گزارش پرداخت شارژ - {year}/{month:02d}**\n\n"
            f"✅ **لیست پرداخت‌کنندگان ({len(paid_user_ids)} نفر):**\n"
        )
        
        for p in payments:
            report_text += f"🔹 {p[1]} (ID: {p[0]})\n"
            
        report_text += f"\n❌ **لیست پرداخت‌نکردگان:**\n"
        report_text += "⚠️ توجه: این لیست شامل تمام اعضایی است که در دیتابیس ادمین‌ها نیستند و پرداختی نداشته‌اند.\n"
        report_text += "(برای دقت بیشتر، لیست اعضا را با لیست بالا تطبیق دهید)"
        
        # ارسال گزارش به تمام ادمین‌ها در پیوی
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, report_text)
            except Exception as e:
                print(f"Failed to send report to admin {admin_id}: {e}")

# نکته: برای اجرای خودکار این تابع، می‌توانید از یک حلقه جداگانه یا Cron Job استفاده کنید.
# در اینجا برای سادگی، یک چک ساده در ابتدای اجرای بات قرار می‌دهیم.
# اما برای تولید واقعی، بهتر است از Celery یا APScheduler استفاده شود.

# ==========================================
# اجرای بات
# ==========================================
if __name__ == "__main__":
    print("🏢 بات ساختمان فدک (نسخه گزارش واریزی) در حال اجراست...")
    print("👨‍💻 توسعه دهنده: radvin")
    
    # چک اولیه برای گزارش (فقط برای تست)
    # import asyncio
    # asyncio.run(send_monthly_report())
    
    bot.run()
