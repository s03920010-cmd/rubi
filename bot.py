"""
بات مدیریت ساختمان فدک - نسخه نهایی متنی
توسعه دهنده: radvin
بدون دکمه شیشه‌ای، با قابلیت گزارش‌گیری خودکار و ثبت رسید
"""

from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update
import sqlite3
import datetime
import os
import asyncio

# ==========================================
# تنظیمات اولیه
# ==========================================
BOT_TOKEN = "CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT"  # توکن را اینجا بگذارید
DB_NAME = "fadak_building.db"
RECEIPTS_DIR = "receipts"

if not os.path.exists(RECEIPTS_DIR):
    os.makedirs(RECEIPTS_DIR)

bot = BotClient(token=BOT_TOKEN)

# دیکشنری برای ذخیره وضعیت موقت کاربران (State Machine)
user_states = {}

# ==========================================
# مدیریت پایگاه داده (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins 
                      (user_id TEXT PRIMARY KEY, role TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS charge_messages 
                      (id INTEGER PRIMARY KEY, text TEXT, card_number TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, description TEXT, registered_by TEXT, date TEXT)''')
    
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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

init_db()

# ==========================================
# هندلرهای بات (دستورات متنی)
# ==========================================

# 1. فعال‌سازی در گروه با پیام "فعال"
@bot.on_update(filters.text("فعال"))
async def activate_in_group(bot: BotClient, update: Update):
    # بررسی اینکه آیا پیام در گروه است یا خیر
    if not hasattr(update, 'chat_id') or not update.chat_id:
        return
        
    user_id = update.new_message.sender_id
    
    # ثبت کاربر به عنوان ادمین
    add_admin(user_id, "admin")
    
    response_text = (
        "✅ **بات ساختمان فدک با موفقیت فعال شد!**\n\n"
        "👤 شما به عنوان مدیر سیستم ثبت شدید.\n\n"
        "📋 **لیست دستورات:**\n"
        "• `شارژ` - مشاهده اطلاعات پرداخت شارژ ماهانه\n"
        "• `واریز` - ارسال رسید واریزی (نام + عکس)\n"
        "• `ثبت هزینه مبلغ توضیحات` - ثبت هزینه جدید (ادمین)\n"
        "• `لیست هزینه ها` - مشاهده تمام هزینه‌ها (ادمین)\n"
        "• `تنظیم شارژ` - تنظیم متن و شماره کارت (ادمین)\n"
        "• `راهنما` - نمایش مجدد این لیست\n\n"
        "💡 **نکته:** روی هر پیام ریپلای بزنید و بنویسید `ادمین` تا بتوانید آن را حذف کنید."
    )
    await update.reply(response_text)

# 2. فعال‌سازی ادمین در پیوی با دستور /admin
@bot.on_update(filters.private, filters.commands("admin"))
async def admin_pv_activation(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    add_admin(user_id, "admin")
    
    response_text = (
        "👤 **شما با موفقیت به عنوان ادمین بات ثبت شدید!**\n\n"
        "اکنون می‌توانید از دستورات مدیریتی در گروه استفاده کنید."
    )
    await update.reply(response_text)

# 3. نمایش راهنما
@bot.on_update(filters.text("راهنما"))
async def show_help(bot: BotClient, update: Update):
    help_text = (
        "📖 **راهنمای دستورات:**\n\n"
        "🔹 `شارژ` - دریافت شماره کارت\n"
        "🔹 `واریز` - ارسال رسید پرداخت\n"
        "🔹 `ثبت هزینه [مبلغ] [توضیحات]`\n"
        "🔹 `لیست هزینه ها`\n"
        "🔹 `تنظیم شارژ` (فقط ادمین)\n"
        "🔹 `ادمین` (ریپلای روی پیام)"
    )
    await update.reply(help_text)

# 4. نمایش اطلاعات شارژ
@bot.on_update(filters.text("شارژ"))
async def show_charge_info(bot: BotClient, update: Update):
    charge_data = get_charge_message()
    if not charge_data:
        await update.reply("📭 هنوز پیام شارژی تنظیم نشده است.")
        return
    
    msg = (
        "💳 **اطلاعات پرداخت شارژ**\n\n"
        f"📝 {charge_data[0]}\n\n"
        f"💳 **شماره کارت:**\n`{charge_data[1]}`\n\n"
        "⚠️ پس از واریز، دستور `واریز` را ارسال کنید."
    )
    await update.reply(msg)

# 5. شروع فرآیند واریز
@bot.on_update(filters.text("واریز"))
async def start_deposit(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    user_states[user_id] = {"step": "waiting_name"}
    await update.reply(
        "💳 **ثبت رسید واریزی**\n\n"
        "لطفاً **نام و نام خانوادگی** خود را ارسال کنید:"
    )

# 6. ثبت هزینه
@bot.on_update(filters.text(lambda t: t.startswith("ثبت هزینه")))
async def register_expense(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ فقط ادمین‌ها می‌توانند هزینه ثبت کنند!")
        return
    
    parts = update.new_message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.reply("❌ فرمت نادرست!\nمثال: `ثبت هزینه 500000 تعمیر آسانسور`")
        return
    
    try:
        amount = float(parts[1].replace(",", ""))
        description = parts[2]
        add_expense(amount, description, user_id)
        await update.reply(f"✅ هزینه {amount:,.0f} تومان ثبت شد.")
    except ValueError:
        await update.reply("❌ مبلغ نامعتبر است.")

# 7. لیست هزینه‌ها
@bot.on_update(filters.text("لیست هزینه ها"))
async def list_expenses(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ دسترسی محدود!")
        return
    
    expenses = get_all_expenses()
    if not expenses:
        await update.reply("📭 هزینه‌ای ثبت نشده است.")
        return
    
    msg = "📊 **لیست هزینه‌ها:**\n\n"
    total = 0
    for exp in expenses:
        total += exp[0]
        msg += f"🔹 {exp[0]:,.0f} ت | {exp[1]}\n"
    msg += f"\n💵 **جمع کل:** {total:,.0f} تومان"
    
    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
    for chunk in chunks:
        await update.reply(chunk)

# 8. تنظیم شارژ
@bot.on_update(filters.text("تنظیم شارژ"))
async def start_set_charge(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ فقط ادمین‌ها!")
        return
    user_states[user_id] = {"step": "waiting_charge_text"}
    await update.reply("📝 لطفاً **متن پیام شارژ** را ارسال کنید:")

# 9. مدیریت ریپلای (حذف پیام)
@bot.on_update(filters.replied, filters.text("ادمین"))
async def manage_replied_message(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    if not is_admin(user_id):
        await update.reply("❌ دسترسی ندارید!")
        return
    
    replied_msg_id = update.new_message.reply_to_message_id
    chat_id = update.chat_id
    user_states[user_id] = {"step": "waiting_delete_confirm", "chat_id": chat_id, "message_id": replied_msg_id}
    await update.reply("🛠 برای **حذف** این پیام، کلمه `حذف` را بفرستید. برای انصراف `لغو`.")

# 10. پردازش State Machine (مراحل متنی)
@bot.on_update(filters.text)
async def handle_state_inputs(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    text = update.new_message.text.strip()
    
    if user_id not in user_states:
        return
    
    user_state = user_states[user_id]
    step = user_state.get("step")
    
    # --- واریز: مرحله 1 (نام) ---
    if step == "waiting_name":
        user_states[user_id]["full_name"] = text
        user_states[user_id]["step"] = "waiting_receipt_photo"
        await update.reply(f"✅ نام {text} ثبت شد.\n\n📸 اکنون **عکس رسید** را ارسال کنید.")
        return

    # --- تنظیم شارژ: مرحله 1 (متن) ---
    if step == "waiting_charge_text":
        user_states[user_id]["text"] = text
        user_states[user_id]["step"] = "waiting_charge_card"
        await update.reply("💳 لطفاً **شماره کارت** را ارسال کنید:")
        return

    # --- تنظیم شارژ: مرحله 2 (کارت) ---
    if step == "waiting_charge_card":
        save_charge_message(user_states[user_id]["text"], text)
        del user_states[user_id]
        await update.reply("✅ پیام شارژ تنظیم شد.")
        return

    # --- حذف پیام: تایید ---
    if step == "waiting_delete_confirm":
        if text == "حذف":
            try:
                await bot.delete_message(user_state["chat_id"], user_state["message_id"])
                await update.reply("✅ پیام حذف شد.")
            except:
                await update.reply("❌ خطا در حذف.")
        elif text == "لغو":
            await update.reply("❌ لغو شد.")
        del user_states[user_id]
        return

# 11. دریافت عکس رسید
@bot.on_update(filters.photo)
async def handle_receipt_photo(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    
    if user_id in user_states and user_states[user_id].get("step") == "waiting_receipt_photo":
        full_name = user_states[user_id].get("full_name")
        photo_file = update.new_message.file
        
        if photo_file and photo_file.file_id:
            file_id = photo_file.file_id
            file_path = f"{RECEIPTS_DIR}/{user_id}_{datetime.datetime.now().timestamp()}.jpg"
            
            try:
                await bot.download_file(file_id, save_as=file_path)
            except Exception as e:
                print(f"Error downloading: {e}")
                file_path = "Failed"

            add_payment(user_id, full_name, file_id, file_path)
            del user_states[user_id]
            
            await update.reply(
                f"✅ **رسید واریزی ثبت شد!**\n\n"
                f"👤 نام: {full_name}\n"
                f"📅 تاریخ: {datetime.datetime.now().strftime('%Y/%m/%d')}"
            )
        else:
            await update.reply("❌ خطا در دریافت عکس.")
            del user_states[user_id]

# ==========================================
# وظیفه زمان‌بندی شده (گزارش ماهانه)
# ==========================================
async def check_and_send_report():
    """هر ساعت چک می‌کند که آیا پنجم ماه است یا خیر"""
    while True:
        now = datetime.datetime.now()
        # اگر پنجم ماه است و ساعت 9 صبح است
        if now.day == 5 and now.hour == 9 and now.minute < 5:
            year = now.year
            month = now.month
            
            payments = get_monthly_payments(year, month)
            admins = get_all_admins()
            
            report_text = f"📊 **گزارش شارژ - {year}/{month:02d}**\n\n"
            report_text += f"✅ **پرداخت‌کنندگان ({len(payments)} نفر):**\n"
            for p in payments:
                report_text += f"🔹 {p[1]}\n"
            
            report_text += "\n❌ **لیست پرداخت‌نکردگان:**\n"
            report_text += "(برای مشاهده لیست کامل اعضا، به پنل مدیریت مراجعه کنید)"
            
            for admin_id in admins:
                try:
                    await bot.send_message(admin_id, report_text)
                except:
                    pass
            
            # خواب برای جلوگیری از ارسال تکراری در همان دقیقه
            await asyncio.sleep(300)
        
        await asyncio.sleep(60) # چک کردن هر دقیقه

# ==========================================
# اجرای بات
# ==========================================
if __name__ == "__main__":
    print("🏢 بات ساختمان فدک در حال اجراست...")
    
    # اجرای همزمان بات و وظیفه زمان‌بندی
    loop = asyncio.get_event_loop()
    loop.create_task(check_and_send_report())
    
    bot.run()
