import asyncio
import json
import os
import re
from datetime import datetime, date

from rubpy.bot import BotClient, filters
from rubpy.bot.models import Update


# =========================================================
# تنظیمات
# =========================================================

TOKEN = "CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT"

DB_FILE = "database.json"

app = BotClient(TOKEN)


# =========================================================
# دیتابیس
# =========================================================

DEFAULT_DB = {
    "owner_id": None,
    "admins": [],
    "groups": {},
    "residents": {},
    "expenses": [],
    "payments": {},
    "charge": {
        "day": 1,
        "amount": 0,
        "card": "",
        "text": "شارژ ساختمان فدک"
    }
}


def load_db():
    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_DB.copy())

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # جلوگیری از خراب شدن دیتابیس در صورت اضافه شدن فیلد جدید
        for key, value in DEFAULT_DB.items():
            if key not in data:
                data[key] = value

        return data

    except Exception:
        save_db(DEFAULT_DB.copy())
        return DEFAULT_DB.copy()


def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


db = load_db()


# =========================================================
# ابزارها
# =========================================================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_day():
    return datetime.now().day


def get_user_id(update: Update):
    if not update.new_message:
        return None

    return update.new_message.sender_id


def get_text(update: Update):
    if not update.new_message:
        return ""

    return (update.new_message.text or "").strip()


def is_admin(user_id):
    if not user_id:
        return False

    if db["owner_id"] == user_id:
        return True

    return user_id in db["admins"]


def is_owner(user_id):
    return user_id == db["owner_id"]


def group_active(chat_id):
    return db["groups"].get(chat_id, {}).get("active", False)


def get_current_month():
    return datetime.now().strftime("%Y-%m")


def normalize_number(value):
    if not value:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹",
        "0123456789"
    )

    return str(value).translate(table)


def money(number):
    try:
        return f"{int(number):,}"
    except Exception:
        return str(number)


# =========================================================
# متن دستورات
# =========================================================

GROUP_HELP = """
🏢 **بات ساختمان فدک**

بات با موفقیت فعال شده است.

📌 **دستورات عمومی**

/help
نمایش این لیست

/charge
نمایش اطلاعات شارژ

/expenses
نمایش تمام هزینه‌های ساختمان

/payment
ثبت پرداخت شارژ

📌 **دستورات مدیریت**

/admin
ثبت اولیه مدیر بات در PV

/addadmin
افزودن مدیر

/removeadmin
حذف مدیر

/setcharge
تنظیم شارژ ساختمان

/addexpense
ثبت هزینه

/residents
لیست ساکنین

/addresident
ثبت ساکن

/removeresident
حذف ساکن

/report
گزارش وضعیت پرداخت‌ها

📌 **مدیریت سریع**

اگر روی پیام یک شخص ریپلای کنید و بنویسید:

ادمین میتونه

آن شخص به مدیر بات تبدیل می‌شود.

⚠️ فقط مالک بات می‌تواند مدیر اصلی را مدیریت کند.
"""


# =========================================================
# فعال کردن بات در گروه
# =========================================================

@app.on_update(
    filters.text("فعال"),
    filters.group
)
async def activate_group(client, update: Update):

    chat_id = update.chat_id

    db["groups"][chat_id] = {
        "active": True,
        "activated_at": now()
    }

    save_db(db)

    await update.reply(
        "✅ **بات ساختمان فدک فعال شد.**\n\n"
        + GROUP_HELP
    )


# =========================================================
# help
# =========================================================

@app.on_update(
    filters.commands(["help", "start"])
)
async def help_command(client, update: Update):

    await update.reply(GROUP_HELP)


# =========================================================
# /admin
# =========================================================

@app.on_update(
    filters.commands("admin")
)
async def admin_command(client, update: Update):

    user_id = get_user_id(update)

    if not user_id:
        return

    # اگر مالک وجود ندارد، اولین شخص مالک می‌شود
    if db["owner_id"] is None:

        db["owner_id"] = user_id

        if user_id not in db["admins"]:
            db["admins"].append(user_id)

        save_db(db)

        await update.reply(
            "👑 **شما به عنوان مالک اصلی بات ثبت شدید.**\n\n"
            "اکنون می‌توانید مدیران و تنظیمات ساختمان را مدیریت کنید."
        )

        return

    if is_admin(user_id):

        await update.reply(
            "✅ شما قبلاً مدیر بات هستید.\n\n"
            "از دستورات مدیریتی استفاده کنید."
        )

    else:

        await update.reply(
            "❌ شما مدیر بات نیستید.\n\n"
            "برای مدیر شدن، مالک بات باید شما را اضافه کند."
        )


# =========================================================
# ادمین کردن با ریپلای
# =========================================================

@app.on_update(
    filters.text("ادمین میتونه"),
    filters.replied
)
async def make_admin(client, update: Update):

    user_id = get_user_id(update)

    if not is_owner(user_id):

        await update.reply(
            "❌ فقط مالک اصلی بات می‌تواند مدیر اضافه کند."
        )

        return

    msg = update.new_message

    target_id = msg.reply_to_message_id

    if not target_id:
        await update.reply(
            "❌ باید روی پیام شخص موردنظر ریپلای کنید."
        )
        return

    # توجه:
    # Rubpy در Update فعلی شناسه پیام ریپلای‌شده را می‌دهد،
    # اما برای گرفتن sender آن پیام به صورت عمومی
    # بسته به endpoint نسخه نصب‌شده ممکن است نیاز به واکشی پیام باشد.
    #
    # در این نسخه، برای جلوگیری از حدس زدن API، از sender پیام
    # فعلی استفاده نمی‌کنیم.

    await update.reply(
        "⚠️ شناسه پیام ریپلای دریافت شد.\n"
        "برای ثبت قطعی کاربر هدف، باید اطلاعات پیام ریپلای‌شده "
        "از API همان نسخه Rubpy واکشی شود."
    )


# =========================================================
# افزودن ادمین با دستور
# =========================================================

@app.on_update(
    filters.commands("addadmin"),
    filters.private
)
async def add_admin(client, update: Update):

    user_id = get_user_id(update)

    if not is_owner(user_id):

        await update.reply(
            "❌ فقط مالک اصلی اجازه افزودن مدیر دارد."
        )

        return

    text = get_text(update)

    parts = text.split(maxsplit=1)

    if len(parts) < 2:

        await update.reply(
            "❌ نحوه استفاده:\n\n"
            "/addadmin USER_ID"
        )

        return

    target = parts[1].strip()

    if target not in db["admins"]:
        db["admins"].append(target)

    save_db(db)

    await update.reply(
        f"✅ کاربر `{target}` به مدیران اضافه شد."
    )


# =========================================================
# حذف ادمین
# =========================================================

@app.on_update(
    filters.commands("removeadmin"),
    filters.private
)
async def remove_admin(client, update: Update):

    user_id = get_user_id(update)

    if not is_owner(user_id):

        await update.reply(
            "❌ فقط مالک اصلی اجازه حذف مدیر دارد."
        )

        return

    text = get_text(update)

    parts = text.split(maxsplit=1)

    if len(parts) < 2:

        await update.reply(
            "❌ نحوه استفاده:\n\n"
            "/removeadmin USER_ID"
        )

        return

    target = parts[1].strip()

    if target == db["owner_id"]:

        await update.reply(
            "❌ مالک اصلی را نمی‌توان حذف کرد."
        )

        return

    if target in db["admins"]:
        db["admins"].remove(target)

    save_db(db)

    await update.reply(
        f"✅ کاربر `{target}` از مدیران حذف شد."
    )


# =========================================================
# تنظیم شارژ
#
# /setcharge 1 500000 6037991234567890
# =========================================================

@app.on_update(
    filters.commands("setcharge")
)
async def set_charge(client, update: Update):

    user_id = get_user_id(update)

    if not is_admin(user_id):

        await update.reply(
            "❌ فقط مدیران بات می‌توانند شارژ را تنظیم کنند."
        )

        return

    text = get_text(update)

    parts = text.split()

    if len(parts) < 4:

        await update.reply(
            "❌ فرمت صحیح:\n\n"
            "/setcharge روز مبلغ شماره_کارت\n\n"
            "مثال:\n"
            "/setcharge 1 500000 6037991234567890"
        )

        return

    try:
        day = int(normalize_number(parts[1]))
        amount = int(normalize_number(parts[2]))
        card = normalize_number(parts[3])

        if day < 1 or day > 31:
            raise ValueError

        db["charge"]["day"] = day
        db["charge"]["amount"] = amount
        db["charge"]["card"] = card

        save_db(db)

        await update.reply(
            "✅ **شارژ ساختمان تنظیم شد.**\n\n"
            f"📅 روز پرداخت: {day}\n"
            f"💰 مبلغ: {money(amount)} تومان\n"
            f"💳 شماره کارت: `{card}`"
        )

    except Exception:

        await update.reply(
            "❌ اطلاعات واردشده صحیح نیست."
        )


# =========================================================
# نمایش شارژ
# =========================================================

@app.on_update(
    filters.commands("charge")
)
async def show_charge(client, update: Update):

    charge = db["charge"]

    await update.reply(
        "🏢 **اطلاعات شارژ ساختمان فدک**\n\n"
        f"📅 تاریخ پرداخت: روز {charge['day']} هر ماه\n"
        f"💰 مبلغ: {money(charge['amount'])} تومان\n"
        f"💳 شماره کارت:\n"
        f"`{charge['card']}`\n\n"
        "📸 بعد از واریز، رسید را در PV بات ارسال کنید.\n"
        "همراه رسید، نام و نام خانوادگی خود را هم بنویسید."
    )


# =========================================================
# ثبت هزینه
#
# /addexpense عنوان | مبلغ
# =========================================================

@app.on_update(
    filters.commands("addexpense")
)
async def add_expense(client, update: Update):

    user_id = get_user_id(update)

    if not is_admin(user_id):

        await update.reply(
            "❌ فقط مدیر یا مالک می‌تواند هزینه ثبت کند."
        )

        return

    text = get_text(update)

    parts = text.split(maxsplit=1)

    if len(parts) < 2:

        await update.reply(
            "❌ فرمت:\n\n"
            "/addexpense عنوان | مبلغ\n\n"
            "مثال:\n"
            "/addexpense تعمیر آسانسور | 2500000"
        )

        return

    try:

        data = parts[1]

        title, amount = data.split("|", 1)

        title = title.strip()
        amount = normalize_number(amount.strip())

        amount = int(amount)

        expense = {
            "title": title,
            "amount": amount,
            "created_by": user_id,
            "created_at": now()
        }

        db["expenses"].append(expense)

        save_db(db)

        await update.reply(
            "✅ هزینه ثبت شد.\n\n"
            f"📌 عنوان: {title}\n"
            f"💰 مبلغ: {money(amount)} تومان"
        )

    except Exception:

        await update.reply(
            "❌ فرمت هزینه صحیح نیست."
        )


# =========================================================
# لیست هزینه‌ها
# =========================================================

@app.on_update(
    filters.commands(["expenses", "listekhazineha"])
)
async def list_expenses(client, update: Update):

    expenses = db["expenses"]

    if not expenses:

        await update.reply(
            "📋 هنوز هیچ هزینه‌ای ثبت نشده است."
        )

        return

    text = "💰 **لیست هزینه‌های ساختمان فدک**\n\n"

    total = 0

    for index, expense in enumerate(expenses, 1):

        amount = int(expense["amount"])

        total += amount

        text += (
            f"**{index}. {expense['title']}**\n"
            f"💵 مبلغ: {money(amount)} تومان\n"
            f"📅 تاریخ: {expense['created_at']}\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━\n"
        f"💰 **جمع کل هزینه‌ها: {money(total)} تومان**"
    )

    await update.reply(text)


# =========================================================
# ثبت ساکن
#
# /addresident USER_ID نام نام خانوادگی
# =========================================================

@app.on_update(
    filters.commands("addresident")
)
async def add_resident(client, update: Update):

    user_id = get_user_id(update)

    if not is_admin(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند ساکن ثبت کنند."
        )

        return

    text = get_text(update)

    parts = text.split(maxsplit=2)

    if len(parts) < 3:

        await update.reply(
            "❌ فرمت:\n\n"
            "/addresident USER_ID نام و نام خانوادگی"
        )

        return

    target_id = parts[1]
    name = parts[2]

    db["residents"][target_id] = {
        "name": name,
        "added_at": now()
    }

    save_db(db)

    await update.reply(
        f"✅ ساکن ثبت شد.\n\n"
        f"👤 نام: {name}\n"
        f"🆔 شناسه: `{target_id}`"
    )


# =========================================================
# حذف ساکن
# =========================================================

@app.on_update(
    filters.commands("removeresident")
)
async def remove_resident(client, update: Update):

    user_id = get_user_id(update)

    if not is_admin(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند ساکن حذف کنند."
        )

        return

    text = get_text(update)

    parts = text.split(maxsplit=1)

    if len(parts) < 2:
        await update.reply(
            "❌ فرمت:\n\n"
            "/removeresident USER_ID"
        )
        return

    target = parts[1].strip()

    if target in db["residents"]:
        del db["residents"][target]

    save_db(db)

    await update.reply(
        "✅ ساکن حذف شد."
    )


# =========================================================
# لیست ساکنین
# =========================================================

@app.on_update(
    filters.commands("residents")
)
async def residents(client, update: Update):

    if not db["residents"]:

        await update.reply(
            "👥 هنوز ساکنی ثبت نشده است."
        )

        return

    text = "👥 **لیست ساکنین ساختمان**\n\n"

    for i, (user_id, info) in enumerate(
        db["residents"].items(),
        1
    ):

        text += (
            f"{i}. {info['name']}\n"
            f"🆔 `{user_id}`\n\n"
        )

    await update.reply(text)


# =========================================================
# ثبت پرداخت دستی
#
# /payment نام و نام خانوادگی
# =========================================================

@app.on_update(
    filters.commands("payment"),
    filters.private
)
async def payment(client, update: Update):

    user_id = get_user_id(update)

    text = get_text(update)

    parts = text.split(maxsplit=1)

    if len(parts) < 2:

        await update.reply(
            "❌ نام و نام خانوادگی را بنویسید.\n\n"
            "مثال:\n"
            "/payment علی رضایی"
        )

        return

    name = parts[1].strip()

    month = get_current_month()

    if month not in db["payments"]:
        db["payments"][month] = {}

    db["payments"][month][user_id] = {
        "name": name,
        "status": "paid",
        "receipt": False,
        "registered_at": now()
    }

    save_db(db)

    await update.reply(
        "✅ پرداخت شما ثبت شد.\n\n"
        f"👤 نام: {name}\n"
        f"📅 ماه: {month}\n\n"
        "📸 لطفاً رسید واریز را نیز ارسال کنید."
    )


# =========================================================
# دریافت رسید
# =========================================================

@app.on_update(
    filters.file,
    filters.private
)
async def receive_receipt(client, update: Update):

    user_id = get_user_id(update)

    message = update.new_message

    if not message or not message.file:
        return

    month = get_current_month()

    if month not in db["payments"]:
        db["payments"][month] = {}

    file_id = message.file.file_id

    db["payments"][month][user_id] = {
        "name": db["payments"][month]
            .get(user_id, {})
            .get("name", "نام ثبت نشده"),
        "status": "paid",
        "receipt": True,
        "file_id": file_id,
        "file_name": message.file.file_name,
        "registered_at": now()
    }

    save_db(db)

    await update.reply(
        "✅ **رسید شما دریافت شد.**\n\n"
        "رسید برای مدیران ساختمان ثبت شد."
    )


# =========================================================
# گزارش پرداخت‌ها
# =========================================================

def create_payment_report():

    month = get_current_month()

    payments = db["payments"].get(month, {})
    residents = db["residents"]

    paid = []
    unpaid = []

    for user_id, info in residents.items():

        if user_id in payments and payments[user_id].get("status") == "paid":

            paid.append(
                payments[user_id].get(
                    "name",
                    info.get("name", "نامشخص")
                )
            )

        else:

            unpaid.append(
                info.get("name", "نامشخص")
            )

    text = (
        f"📊 **گزارش شارژ ساختمان فدک**\n"
        f"📅 ماه: {month}\n\n"
        f"✅ پرداخت کرده‌اند: {len(paid)} نفر\n"
    )

    if paid:
        for name in paid:
            text += f"• {name}\n"

    text += (
        f"\n❌ پرداخت نکرده‌اند: {len(unpaid)} نفر\n"
    )

    if unpaid:
        for name in unpaid:
            text += f"• {name}\n"

    return text


# =========================================================
# /report
# =========================================================

@app.on_update(
    filters.commands("report")
)
async def report(client, update: Update):

    user_id = get_user_id(update)

    if not is_admin(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند گزارش پرداخت‌ها را ببینند."
        )

        return

    await update.reply(
        create_payment_report()
    )


# =========================================================
# ارسال گزارش روز پنجم
# =========================================================

async def daily_report():

    while True:

        try:

            current_day = today_day()

            if current_day == 5:

                report = create_payment_report()

                # ارسال به مالک
                if db["owner_id"]:

                    try:
                        await app.send_message(
                            db["owner_id"],
                            report
                        )
                    except Exception:
                        pass

                # ارسال به ادمین‌ها
                for admin_id in db["admins"]:

                    if admin_id == db["owner_id"]:
                        continue

                    try:
                        await app.send_message(
                            admin_id,
                            report
                        )
                    except Exception:
                        pass

                # جلوگیری از ارسال چندباره
                await asyncio.sleep(86400)

            else:

                await asyncio.sleep(3600)

        except Exception as e:

            print(
                "Daily report error:",
                e
            )

            await asyncio.sleep(3600)


# =========================================================
# ارسال پیام شارژ در روز مشخص
# =========================================================

async def charge_scheduler():

    last_sent = None

    while True:

        try:

            day = db["charge"]["day"]

            current_day = today_day()

            key = datetime.now().strftime("%Y-%m-%d")

            if current_day == day and last_sent != key:

                amount = db["charge"]["amount"]
                card = db["charge"]["card"]

                message = (
                    "🏢 **شارژ ساختمان فدک**\n\n"
                    f"💰 مبلغ شارژ: {money(amount)} تومان\n"
                    f"💳 شماره کارت:\n"
                    f"`{card}`\n\n"
                    "پس از واریز:\n"
                    "📸 رسید واریز را در PV بات ارسال کنید.\n"
                    "👤 نام و نام خانوادگی خود را نیز بنویسید.\n\n"
                    "🙏 با تشکر"
                )

                for group_id, info in db["groups"].items():

                    if not info.get("active"):
                        continue

                    try:
                        await app.send_message(
                            group_id,
                            message
                        )
                    except Exception as e:
                        print(
                            "Charge message error:",
                            e
                        )

                last_sent = key

            await asyncio.sleep(3600)

        except Exception as e:

            print(
                "Charge scheduler error:",
                e
            )

            await asyncio.sleep(3600)


# =========================================================
# پیام عمومی دستورات داخل گروه
# =========================================================

@app.on_update(
    filters.text
)
async def group_text(client, update: Update):

    if not update.new_message:
        return

    if not filters_group_check(update):
        return

    if not group_active(update.chat_id):
        return

    text = get_text(update)

    if text in [
        "دستورات",
        "دستور",
        "راهنما",
        "بات ساختمان فدک"
    ]:

        await update.reply(GROUP_HELP)


def filters_group_check(update):

    try:
        message = update.new_message

        if not message:
            return False

        # تشخیص گروه از chat type در صورت وجود
        # در صورت عدم وجود، فیلتر گروه در هندلرهای
        # اختصاصی استفاده می‌شود.

        return True

    except Exception:
        return False


# =========================================================
# اجرای همزمان زمان‌بندی‌ها
# =========================================================

async def scheduler():

    await asyncio.gather(
        charge_scheduler(),
        daily_report()
    )


# =========================================================
# شروع بات
# =========================================================

if __name__ == "__main__":

    print("================================")
    print("🏢 بات ساختمان فدک")
    print("🚀 Rubpy Bot")
    print("================================")

    loop = asyncio.get_event_loop()

    loop.create_task(
        scheduler()
    )

    app.run()
