from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import Update, Keypad, KeypadRow, Button
from rubpy.bot.enums import ButtonTypeEnum
import json
import os
from datetime import datetime

# نام بات و فایل ذخیره‌سازی
BOT_NAME = "ساختمان فدک"
DATA_FILE = "fadak_data.json"

def load_data():
    """بارگذاری داده‌ها از فایل"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "admins": [],
        "expenses": [],
        "payments": {},
        "scheduled_messages": {},
        "active_groups": []
    }

def save_data(data):
    """ذخیره داده‌ها در فایل"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

# ایجاد نمونه بات
bot = BotClient("CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT")

@bot.on_update(filters.text)
async def handle_all_messages(bot, update: Update):
    """مدیریت تمام پیام‌ها"""
    if not update.new_message:
        return
    
    data = load_data()
    user_id = update.new_message.sender_id
    chat_id = update.chat_id
    message_text = update.new_message.text.strip() if update.new_message.text else ""
    
    # بررسی اینکه پیام در گروه است یا خصوصی
    is_private = update.new_message.chat_type == "private" if hasattr(update.new_message, 'chat_type') else False
    is_group = update.new_message.chat_type in ["group", "supergroup"] if hasattr(update.new_message, 'chat_type') else False
    
    # فعال‌سازی بات در گروه با پیام "فعال"
    if is_group and message_text == "فعال":
        if chat_id not in data["active_groups"]:
            data["active_groups"].append(chat_id)
        
        # اگر کاربر قبلاً ادمین نیست، اضافه شود
        if user_id not in data["admins"]:
            data["admins"].append(user_id)
        
        save_data(data)
        
        commands_list = """🏢 *بات ساختمان فدک فعال شد!*

📋 *لیست دستورات:*

/admin - ثبت به عنوان ادمین
/expense [مبلغ] [توضیحات] - ثبت هزینه
/expenses - نمایش لیست هزینه‌ها
/set_charge [پیام شارژ] - تنظیم پیام شارژ ماهانه
/payments - مشاهده وضعیت پرداخت‌ها
/remind [نام کاربر] - یادآوری پرداخت به کاربر
/help - نمایش راهنما

✅ بات با موفقیت فعال شد!"""
        
        await update.reply(commands_list)
        return
    
    # دستور /admin - هر کسی بزند ادمین می‌شود
    if message_text == "/admin":
        if user_id not in data["admins"]:
            data["admins"].append(user_id)
            save_data(data)
            await update.reply("✅ شما به عنوان ادمین ثبت شدید!\n\nاکنون می‌توانید از دستورات مدیریتی استفاده کنید.")
        else:
            await update.reply("✅ شما قبلاً ادمین هستید.")
        return
    
    # بررسی ادمین بودن برای دستورات مدیریتی
    if not is_admin(user_id, data):
        # اگر کاربر عادی است و پیام ریپلای شده
        if update.new_message.reply_to_message_id:
            await update.reply("ادمین می‌تواند ویژگی‌های بات را مدیریت کند.")
        return
    
    # ===== دستورات ادمین =====
    
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
        
        for uid, payment_info in data["payments"].items():
            status = "✅ پرداخت شده" if payment_info.get("paid", False) else "❌ پرداخت نشده"
            payments_text += f"👤 کاربر: {payment_info.get('name', 'نامشخص')}\n"
            payments_text += f"   وضعیت: {status}\n"
            payments_text += f"   تاریخ: {format_date(payment_info.get('date', ''))}\n\n"
        
        await update.reply(payments_text)
        return
    
    # یادآوری پرداخت به کاربر خاص
    if message_text.startswith("/remind"):
        parts = message_text.split(maxsplit=1)
        if len(parts) >= 2:
            target_name = parts[1].strip()
            
            # جستجوی کاربر بر اساس نام
            found_user = None
            for uid, info in data["payments"].items():
                if info.get("name", "").lower() == target_name.lower():
                    found_user = uid
                    break
            
            if found_user:
                await update.reply(f"✅ یادآوری برای {target_name} ارسال شد.")
            else:
                await update.reply(f"❌ کاربری با نام '{target_name}' یافت نشد.")
        else:
            await update.reply("❌ فرمت نادرست!\nاستفاده صحیح: /remind [نام کاربر]")
        return
    
    # راهنما
    if message_text == "/help":
        help_text = """🏢 *راهنمای بات ساختمان فدک*

👨‍💼 *دستورات ادمین:*
/admin - ثبت به عنوان ادمین
/expense [مبلغ] [توضیحات] - ثبت هزینه
/expenses - نمایش لیست هزینه‌ها
/set_charge [پیام] - تنظیم پیام شارژ ماهانه
/payments - مشاهده وضعیت پرداخت‌ها
/remind [نام] - یادآوری پرداخت به کاربر

👥 *دستورات کاربران:*
فعال - فعال‌سازی بات در گروه
پرداخت [نام] [رسید] - ثبت رسید پرداخت

📅 *یادآوری خودکار:*
بات هر ماه در روز پنجم، وضعیت پرداخت‌ها را به ادمین‌ها اطلاع می‌دهد."""
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

if __name__ == "__main__":
    print(f"🏢 بات {BOT_NAME} در حال اجراست...")
    bot.run()
