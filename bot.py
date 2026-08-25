from rubpy.bot import BotClient, filters
from rubpy.bot.models import Update
import json
import os
from datetime import datetime, timedelta

# نام بات و فایل ذخیره‌سازی
BOT_NAME = "ساختمان فدک"
DATA_FILE = "fadak_data.json"

# لیست ادمین‌ها (شماره تلفن یا شناسه کاربری)
ADMINS = []

def load_data():
    """بارگذاری داده‌ها از فایل"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "admins": [],
        "expenses": [],
        "payments": {},
        "scheduled_messages": {}
    }

def save_data(data):
    """ذخیره داده‌ها در فایل"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_id(update):
    """دریافت شناسه کاربر"""
    return update.new_message.author_id

def is_admin(user_id, data):
    """بررسی آیا کاربر ادمین است"""
    return user_id in data["admins"]

def format_date(date_str):
    """فرمت تاریخ برای نمایش"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y/%m/%d")
    except:
        return date_str

app = BotClient("CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT")

@app.on_update(filters.text)
async def handle_messages(client, update: Update):
    """مدیریت تمام پیام‌ها"""
    data = load_data()
    user_id = get_user_id(update)
    message_text = update.new_message.text.strip()
    
    # بررسی اینکه پیام در گروه است یا خصوصی
    is_private = update.new_message.chat_type == "private"
    is_group = update.new_message.chat_type in ["group", "supergroup"]
    
    # فعال‌سازی بات در گروه
    if is_group and message_text == "فعال":
        if user_id not in data["admins"]:
            data["admins"].append(user_id)
            save_data(data)
        
        commands_list = """
🏢 *بات ساختمان فدک فعال شد!*

📋 *لیست دستورات:*

/admin - ثبت به عنوان ادمین
/expense [مبلغ] [توضیحات] - ثبت هزینه
/expenses - نمایش لیست هزینه‌ها
/set_charge [پیام شارژ] - تنظیم پیام شارژ ماهانه
/payments - مشاهده وضعیت پرداخت‌ها
/help - نمایش راهنما

✅ بات با موفقیت فعال شد!
        """
        await update.reply(commands_list)
        return
    
    # دستور /admin در پیوی یا گروه
    if message_text == "/admin":
        if user_id not in data["admins"]:
            data["admins"].append(user_id)
            save_data(data)
            await update.reply("✅ شما به عنوان ادمین ثبت شدید!")
        else:
            await update.reply("✅ شما قبلاً ادمین هستید.")
        return
    
    # بررسی ادمین بودن برای دستورات مدیریتی
    if not is_admin(user_id, data):
        # اگر کاربر عادی است و پیام ریپلای شده
        if update.new_message.reply_to_message_id:
            await update.reply("ادمین می‌تواند ویژگی‌های بات را مدیریت کند.")
        return
    
    # دستورات ادمین
    
    # ثبت هزینه
    if message_text.startswith("/expense"):
        parts = message_text.split(maxsplit=2)
        if len(parts) >= 3:
            try:
                amount = float(parts[1])
                description = parts[2]
                
                expense = {
                    "id": len(data["expenses"]) + 1,
                    "amount": amount,
                    "description": description,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "admin_id": user_id
                }
                
                data["expenses"].append(expense)
                save_data(data)
                
                await update.reply(f"✅ هزینه ثبت شد:\n💰 مبلغ: {amount} تومان\n📝 توضیحات: {description}")
            except ValueError:
                await update.reply("❌ فرمت نادرست!\nاستفاده صحیح: /expense [مبلغ] [توضیحات]")
        else:
            await update.reply("❌ فرمت نادرست!\nاستفاده صحیح: /expense [مبلغ] [توضیحات]")
        return
    
    # نمایش لیست هزینه‌ها
    if message_text == "/expenses":
        if not data["expenses"]:
            await update.reply("📭 هیچ هزینه‌ای ثبت نشده است.")
            return
        
        expenses_text = "📊 *لیست هزینه‌ها:*\n\n"
        total = 0
        
        for expense in data["expenses"]:
            expenses_text += f"🔹 #{expense['id']} | 💰 {expense['amount']} تومان\n"
            expenses_text += f"   📝 {expense['description']}\n"
            expenses_text += f"   📅 {format_date(expense['date'])}\n\n"
            total += expense['amount']
        
        expenses_text += f"\n💎 *جمع کل: {total} تومان*"
        await update.reply(expenses_text)
        return
    
    # تنظیم پیام شارژ
    if message_text.startswith("/set_charge"):
        if len(message_text) > 12:
            charge_message = message_text[12:].strip()
            data["scheduled_messages"]["charge"] = charge_message
            save_data(data)
            await update.reply("✅ پیام شارژ ماهانه با موفقیت تنظیم شد!")
        else:
            await update.reply("❌ لطفاً پیام شارژ را بعد از دستور وارد کنید.\nمثال: /set_charge لطفاً شارژ ماه خود را پرداخت کنید. شماره کارت: 1234-5678-9012-3456")
        return
    
    # مشاهده وضعیت پرداخت‌ها
    if message_text == "/payments":
        if not data["payments"]:
            await update.reply("📭 هیچ پرداختی ثبت نشده است.")
            return
        
        payments_text = "💳 *وضعیت پرداخت‌ها:*\n\n"
        
        for user_id_str, payment_info in data["payments"].items():
            status = "✅ پرداخت شده" if payment_info.get("paid", False) else "❌ پرداخت نشده"
            payments_text += f"👤 کاربر: {payment_info.get('name', 'نامشخص')}\n"
            payments_text += f"   وضعیت: {status}\n"
            payments_text += f"   تاریخ: {format_date(payment_info.get('date', ''))}\n\n"
        
        await update.reply(payments_text)
        return
    
    # راهنما
    if message_text == "/help":
        help_text = """
🏢 *راهنمای بات ساختمان فدک*

👨‍💼 *دستورات ادمین:*
/admin - ثبت به عنوان ادمین
/expense [مبلغ] [توضیحات] - ثبت هزینه
/expenses - نمایش لیست هزینه‌ها
/set_charge [پیام] - تنظیم پیام شارژ ماهانه
/payments - مشاهده وضعیت پرداخت‌ها

👥 *دستورات کاربران:*
فعال - فعال‌سازی بات در گروه
پرداخت [نام] [رسید] - ثبت رسید پرداخت

📅 *یادآوری خودکار:*
بات هر ماه در روز پنجم، وضعیت پرداخت‌ها را به ادمین‌ها اطلاع می‌دهد.
        """
        await update.reply(help_text)
        return
    
    # ثبت پرداخت توسط کاربران
    if message_text.startswith("پرداخت"):
        parts = message_text.split(maxsplit=2)
        if len(parts) >= 3:
            name = parts[1]
            receipt = parts[2]
            
            data["payments"][str(user_id)] = {
                "name": name,
                "receipt": receipt,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "paid": True
            }
            save_data(data)
            
            await update.reply(f"✅ پرداخت شما ثبت شد!\n👤 نام: {name}\n📅 تاریخ: {format_date(datetime.now().strftime('%Y-%m-%d'))}")
        else:
            await update.reply("❌ فرمت نادرست!\nاستفاده صحیح: پرداخت [نام] [رسید]")
        return

# تابع یادآوری ماهانه (باید به صورت جداگانه اجرا شود)
async def monthly_reminder():
    """یادآوری ماهانه پرداخت‌ها"""
    data = load_data()
    today = datetime.now()
    
    # اگر امروز پنجم ماه است
    if today.day == 5:
        admins = data["admins"]
        payments = data["payments"]
        
        paid_users = []
        unpaid_users = []
        
        for user_id, info in payments.items():
            if info.get("paid", False):
                paid_users.append(info.get("name", "نامشخص"))
            else:
                unpaid_users.append(info.get("name", "نامشخص"))
        
        reminder_text = f"📅 *یادآوری ماهانه پرداخت‌ها*\n\n"
        reminder_text += f"✅ پرداخت‌کنندگان ({len(paid_users)} نفر):\n"
        for name in paid_users:
            reminder_text += f"• {name}\n"
        
        reminder_text += f"\n❌ پرداخت‌نکردگان ({len(unpaid_users)} نفر):\n"
        for name in unpaid_users:
            reminder_text += f"• {name}\n"
        
        # ارسال به تمام ادمین‌ها
        for admin_id in admins:
            try:
                # اینجا باید منطق ارسال پیام به ادمین‌ها اضافه شود
                pass
            except:
                pass

if __name__ == "__main__":
    print(f"🏢 بات {BOT_NAME} در حال اجراست...")
    app.run()
