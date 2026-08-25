"""
بات مدیریت ساختمان فدک
توسعه دهنده: Developer
ساخته شده با کتابخانه Rubpy و رعایت استانداردهای API روبیکا
"""

from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Keypad, KeypadRow, Button, Update
from rubpy.bot.enums import ButtonTypeEnum
import sqlite3
import datetime

# ==========================================
# تنظیمات اولیه
# ==========================================
BOT_TOKEN = "CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT"
DB_NAME = "fadak_building.db"

bot = BotClient(token=BOT_TOKEN)

# دیکشنری برای مدیریت مراحل دریافت اطلاعات (State Machine)
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

init_db()

# ==========================================
# توابع ساخت دکمه‌های شیشه‌ای (Inline Keypad)
# ==========================================
def get_main_group_keypad():
    return Keypad(rows=[
        KeypadRow(buttons=[
            Button(id="show_charge", type=ButtonTypeEnum.SIMPLE, button_text="💳 مشاهده شارژ ماهانه")
        ]),
        KeypadRow(buttons=[
            Button(id="admin_panel", type=ButtonTypeEnum.SIMPLE, button_text="⚙️ پنل مدیریت (ادمین/کالک)")
        ])
    ])

def get_admin_panel_keypad():
    return Keypad(rows=[
        KeypadRow(buttons=[
            Button(id="set_charge", type=ButtonTypeEnum.SIMPLE, button_text="📝 تنظیم پیام شارژ"),
            Button(id="add_expense", type=ButtonTypeEnum.SIMPLE, button_text="💰 ثبت هزینه جدید")
        ]),
        KeypadRow(buttons=[
            Button(id="list_expenses", type=ButtonTypeEnum.SIMPLE, button_text="📊 مشاهده تمام هزینه‌ها")
        ])
    ])

def get_manage_message_keypad(chat_id: str, message_id: str):
    return Keypad(rows=[
        KeypadRow(buttons=[
            Button(id=f"del_msg:{chat_id}:{message_id}", type=ButtonTypeEnum.SIMPLE, button_text="🗑 حذف این پیام")
        ])
    ])

# ==========================================
# هندلرهای اصلی بات
# ==========================================

# 1. فعال‌سازی در گروه با پیام متنی "فعال"
@bot.on_update(filters.group, filters.text("فعال"))
async def activate_in_group(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    add_admin(user_id, "admin")
    
    text = (
        "✅ **بات ساختمان فدک با موفقیت فعال شد!**\n\n"
        "👤 شما به عنوان مدیر سیستم ثبت شدید.\n"
        "از منوی دکمه‌ای زیر برای مدیریت استفاده کنید:"
    )
    await update.reply(text, inline_keypad=get_main_group_keypad())

# 2. فعال‌سازی ادمین در پیوی با دستور /admin
@bot.on_update(filters.private, filters.commands("admin"))
async def admin_pv_activation(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    add_admin(user_id, "admin")
    
    text = "👤 **شما با موفقیت به عنوان ادمین بات ثبت شدید!**\nپنل مدیریت در زیر برای شما باز شد:"
    await update.reply(text, inline_keypad=get_admin_panel_keypad())

# 3. مدیریت پیام با ریپلای و نوشتن "ادمین"
@bot.on_update(filters.group, filters.replied, filters.text("ادمین"))
async def manage_replied_message(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    
    if not is_admin(user_id):
        await update.reply("❌ شما دسترسی ادمین برای مدیریت پیام‌ها را ندارید!")
        return
    
    replied_msg_id = update.new_message.reply_to_message_id
    chat_id = update.chat_id
    
    await update.reply(
        "🛠 **گزینه‌های مدیریت پیام انتخاب‌شده:**",
        inline_keypad=get_manage_message_keypad(chat_id, replied_msg_id)
    )

# 4. پردازش کلیک روی دکمه‌های شیشه‌ای (Inline Buttons)
@bot.on_update(filters.has_aux_data)
async def handle_inline_buttons(bot: BotClient, update: Update):
    # تشخیص نوع آپدیت (کلیک روی دکمه شیشه‌ای معمولاً به صورت inline_message می‌آید)
    if hasattr(update, 'inline_message') and update.inline_message:
        user_id = update.inline_message.sender_id
        chat_id = update.inline_message.chat_id
        btn_id = update.inline_message.aux_data.button_id
    elif hasattr(update, 'new_message') and update.new_message and update.new_message.aux_data and update.new_message.aux_data.button_id:
        user_id = update.new_message.sender_id
        chat_id = update.chat_id
        btn_id = update.new_message.aux_data.button_id
    else:
        return

    # --- حذف پیام ---
    if btn_id.startswith("del_msg:"):
        if not is_admin(user_id):
            await update.reply("❌ دسترسی غیرمجاز!")
            return
        
        parts = btn_id.split(":")
        if len(parts) == 3:
            target_chat_id = parts[1]
            target_msg_id = parts[2]
            try:
                await bot.delete_message(target_chat_id, target_msg_id)
                await update.reply("✅ پیام با موفقیت حذف شد.")
            except Exception:
                await update.reply("❌ خطا در حذف پیام. اطمینان حاصل کنید بات در آن گروه ادمین است.")

    # --- پنل مدیریت ---
    elif btn_id == "admin_panel":
        if not is_admin(user_id):
            await update.reply("❌ فقط ادمین‌ها و کالک‌ها دسترسی به این بخش را دارند!")
            return
        await update.reply("⚙️ به پنل مدیریت خوش آمدید. یکی از گزینه‌ها را انتخاب کنید:", inline_keypad=get_admin_panel_keypad())

    # --- تنظیم پیام شارژ ---
    elif btn_id == "set_charge":
        if not is_admin(user_id):
            await update.reply("❌ دسترسی غیرمجاز!")
            return
        user_states[user_id] = {"step": "waiting_charge_text"}
        await update.reply("📝 لطفاً **متن پیام یادآوری شارژ** را ارسال کنید:\n(مثال: ساکنین محترم، لطفاً شارژ ماه جاری را پرداخت نمایید.)")

    # --- ثبت هزینه ---
    elif btn_id == "add_expense":
        if not is_admin(user_id):
            await update.reply("❌ فقط ادمین‌ها و کالک‌ها می‌توانند هزینه ثبت کنند!")
            return
        user_states[user_id] = {"step": "waiting_expense_amount"}
        await update.reply("💰 لطفاً **مبلغ هزینه** را به عدد (تومان) وارد کنید:\n(مثال: 500000)")

    # --- لیست تمام هزینه‌ها ---
    elif btn_id == "list_expenses":
        if not is_admin(user_id):
            await update.reply("❌ دسترسی غیرمجاز!")
            return
        
        expenses = get_all_expenses()
        if not expenses:
            await update.reply("📭 هنوز هیچ هزینه‌ای در سیستم ثبت نشده است.")
            return
        
        msg = "📊 **لیست کامل هزینه‌های ساختمان فدک:**\n\n"
        total = 0
        for exp in expenses:
            total += exp[0]
            msg += f"🔹 {exp[0]:,.0f} ت | {exp[1]}\n   👤 {exp[2]} | 📅 {exp[3]}\n"
        
        msg += f"\n💵 **جمع کل:** {total:,.0f} تومان"
        
        # تقسیم پیام به بخش‌های 4000 کاراکتری برای جلوگیری از خطای طولانی بودن پیام در روبیکا
        chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
        for i, chunk in enumerate(chunks):
            await update.reply(chunk)

    # --- نمایش اطلاعات شارژ ---
    elif btn_id == "show_charge":
        charge_data = get_charge_message()
        if not charge_data:
            await update.reply("📭 هنوز پیام شارژی توسط مدیریت تنظیم نشده است.")
            return
        
        msg = (
            "💳 **اطلاعات پرداخت شارژ ساختمان فدک**\n\n"
            f"📝 {charge_data[0]}\n\n"
            f"💳 **شماره کارت:**\n`{charge_data[1]}`\n\n"
            "⚠️ لطفاً پس از واریز، تصویر فیش را برای مدیریت ارسال کنید."
        )
        await update.reply(msg)


# 5. هندلر دریافت متن برای مراحل ثبت اطلاعات (State Management)
@bot.on_update(filters.text)
async def handle_state_inputs(bot: BotClient, update: Update):
    user_id = update.new_message.sender_id
    text = update.new_message.text.strip()
    
    # اگر کاربر در حالت ثبت اطلاعات نباشد، خارج شو
    if user_id not in user_states:
        return
    
    user_state = user_states[user_id]
    
    # مرحله 1: دریافت متن پیام شارژ
    if user_state.get("step") == "waiting_charge_text":
        user_states[user_id]["text"] = text
        user_states[user_id]["step"] = "waiting_charge_card"
        await update.reply("💳 عالی! اکنون **شماره کارت** مقصد را ارسال کنید:\n(مثال: 6037-9911-1234-5678)")
        return

    # مرحله 2: دریافت شماره کارت شارژ
    if user_state.get("step") == "waiting_charge_card":
        card_number = text
        charge_text = user_states[user_id].get("text", "")
        
        save_charge_message(charge_text, card_number)
        del user_states[user_id]
        
        await update.reply(
            "✅ **پیام شارژ با موفقیت تنظیم و ذخیره شد!**",
            inline_keypad=get_admin_panel_keypad()
        )
        return

    # مرحله 1: دریافت مبلغ هزینه
    if user_state.get("step") == "waiting_expense_amount":
        try:
            amount = float(text.replace(",", ""))
            user_states[user_id]["amount"] = amount
            user_states[user_id]["step"] = "waiting_expense_desc"
            await update.reply(f"📝 مبلغ {amount:,.0f} تومان ثبت شد. اکنون **توضیحات هزینه** را بنویسید:\n(مثال: تعمیر آسانسور)")
        except ValueError:
            await update.reply("❌ مبلغ وارد شده معتبر نیست! لطفاً فقط عدد وارد کنید (مثال: 500000)")
        return

    # مرحله 2: دریافت توضیحات هزینه
    if user_state.get("step") == "waiting_expense_desc":
        description = text
        amount = user_states[user_id].get("amount", 0)
        
        add_expense(amount, description, user_id)
        del user_states[user_id]
        
        await update.reply(
            f"✅ **هزینه با موفقیت ثبت شد!**\n\n"
            f"💰 مبلغ: {amount:,.0f} تومان\n"
            f"📝 توضیحات: {description}\n"
            f"📅 تاریخ: {datetime.datetime.now().strftime('%Y/%m/%d')}",
            inline_keypad=get_admin_panel_keypad()
        )
        return


# ==========================================
# اجرای بات
# ==========================================
if __name__ == "__main__":
    print("🏢 بات ساختمان فدک در حال اجراست...")
    print("💡 برای فعال‌سازی در گروه، پیام «فعال» را ارسال کنید.")
    print("💡 برای تعریف ادمین در پیوی، دستور /admin را ارسال کنید.")
    
    bot.run()
