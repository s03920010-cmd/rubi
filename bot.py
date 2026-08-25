import asyncio
import json
import os
from datetime import datetime

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
        "card": ""
    }
}


def load_database():
    if not os.path.exists(DB_FILE):
        save_database(DEFAULT_DB)
        return DEFAULT_DB.copy()

    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        for key, value in DEFAULT_DB.items():
            if key not in data:
                data[key] = value

        return data

    except Exception:
        save_database(DEFAULT_DB)
        return DEFAULT_DB.copy()


def save_database(data):
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


db = load_database()


# =========================================================
# ابزارهای کمکی
# =========================================================

def زمان():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ماه_فعلی():
    return datetime.now().strftime("%Y-%m")


def شناسه_کاربر(update):
    try:
        return str(update.new_message.sender_id)
    except Exception:
        return None


def متن(update):
    try:
        return (update.new_message.text or "").strip()
    except Exception:
        return ""


def مدیر_است(user_id):
    if not user_id:
        return False

    user_id = str(user_id)

    return (
        str(db["owner_id"]) == user_id
        or user_id in [str(x) for x in db["admins"]]
    )


def مالک_است(user_id):
    if not user_id:
        return False

    return str(db["owner_id"]) == str(user_id)


def مبلغ(عدد):
    try:
        return f"{int(عدد):,}"
    except Exception:
        return str(عدد)


def عدد_فارسی_به_انگلیسی(value):
    if not value:
        return ""

    return str(value).translate(
        str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹",
            "0123456789"
        )
    )


# =========================================================
# لیست دستورات
# =========================================================

دستورات = """
🏢 **بات ساختمان فدک**

━━━━━━━━━━━━━━━━━━

📋 دستورات عمومی:

/راهنما
نمایش لیست دستورات

/شارژ
نمایش مبلغ و اطلاعات شارژ

/هزینه‌ها
نمایش تمام هزینه‌های ساختمان

/پرداخت
ثبت پرداخت شارژ

━━━━━━━━━━━━━━━━━━

👑 دستورات مدیریتی:

/مدیر
ثبت یا بررسی مدیر بات

/افزودن_مدیر
افزودن مدیر جدید

/حذف_مدیر
حذف مدیر

/تنظیم_شارژ
تنظیم روز، مبلغ و شماره کارت

/ثبت_هزینه
ثبت هزینه ساختمان

/ساکنین
نمایش لیست ساکنین

/افزودن_ساکن
افزودن ساکن

/حذف_ساکن
حذف ساکن

/گزارش
گزارش پرداخت و عدم پرداخت

━━━━━━━━━━━━━━━━━━

⚡ مدیریت سریع:

روی پیام یک شخص ریپلای کنید و بنویسید:

ادمین میتونه

━━━━━━━━━━━━━━━━━━

📸 برای پرداخت شارژ:

رسید واریز را در PV بات ارسال کنید
و همراه آن نام و نام خانوادگی خود را بنویسید.
"""


# =========================================================
# فعال کردن بات در گروه
# =========================================================

@app.on_update(
    filters.text("فعال"),
    filters.group
)
async def فعال_کردن(client, update: Update):

    chat_id = str(update.chat_id)

    db["groups"][chat_id] = {
        "active": True,
        "activated_at": زمان()
    }

    save_database(db)

    await update.reply(
        "✅ بات ساختمان فدک فعال شد.\n\n" +
        دستورات
    )


# =========================================================
# راهنما
# =========================================================

@app.on_update(
    filters.commands("راهنما")
)
async def راهنما(client, update: Update):

    await update.reply(دستورات)


# =========================================================
# مدیر
# =========================================================

@app.on_update(
    filters.commands("مدیر")
)
async def مدیر(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not user_id:
        return

    # اولین نفری که /مدیر می‌زند مالک می‌شود
    if db["owner_id"] is None:

        db["owner_id"] = user_id

        if user_id not in db["admins"]:
            db["admins"].append(user_id)

        save_database(db)

        await update.reply(
            "👑 شما به عنوان مالک اصلی بات ساختمان فدک ثبت شدید.\n\n"
            "اکنون می‌توانید مدیران و تنظیمات ساختمان را مدیریت کنید."
        )

        return

    if مدیر_است(user_id):

        await update.reply(
            "✅ شما مدیر بات هستید."
        )

    else:

        await update.reply(
            "❌ شما مدیر بات نیستید."
        )


# =========================================================
# افزودن مدیر
# =========================================================

@app.on_update(
    filters.commands("افزودن_مدیر")
)
async def افزودن_مدیر(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مالک_است(user_id):

        await update.reply(
            "❌ فقط مالک اصلی بات می‌تواند مدیر اضافه کند."
        )

        return

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split(maxsplit=1)

    if len(بخش‌ها) < 2:

        await update.reply(
            "❌ روش استفاده:\n\n"
            "/افزودن_مدیر شناسه_کاربر"
        )

        return

    هدف = بخش‌ها[1].strip()

    if هدف not in db["admins"]:
        db["admins"].append(هدف)

    save_database(db)

    await update.reply(
        f"✅ کاربر {هدف} به مدیران اضافه شد."
    )


# =========================================================
# حذف مدیر
# =========================================================

@app.on_update(
    filters.commands("حذف_مدیر")
)
async def حذف_مدیر(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مالک_است(user_id):

        await update.reply(
            "❌ فقط مالک اصلی می‌تواند مدیر حذف کند."
        )

        return

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split(maxsplit=1)

    if len(بخش‌ها) < 2:

        await update.reply(
            "❌ روش استفاده:\n\n"
            "/حذف_مدیر شناسه_کاربر"
        )

        return

    هدف = بخش‌ها[1].strip()

    if هدف == str(db["owner_id"]):

        await update.reply(
            "❌ مالک اصلی را نمی‌توان حذف کرد."
        )

        return

    if هدف in db["admins"]:
        db["admins"].remove(هدف)

    save_database(db)

    await update.reply(
        "✅ مدیر حذف شد."
    )


# =========================================================
# تنظیم شارژ
# =========================================================

@app.on_update(
    filters.commands("تنظیم_شارژ")
)
async def تنظیم_شارژ(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند شارژ را تنظیم کنند."
        )

        return

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split()

    if len(بخش‌ها) < 4:

        await update.reply(
            "❌ روش استفاده:\n\n"
            "/تنظیم_شارژ روز مبلغ شماره_کارت\n\n"
            "مثال:\n"
            "/تنظیم_شارژ 1 500000 6037991234567890"
        )

        return

    try:

        روز = int(
            عدد_فارسی_به_انگلیسی(بخش‌ها[1])
        )

        مقدار = int(
            عدد_فارسی_به_انگلیسی(بخش‌ها[2])
        )

        کارت = عدد_فارسی_به_انگلیسی(بخش‌ها[3])

        if روز < 1 or روز > 31:
            raise ValueError

        db["charge"]["day"] = روز
        db["charge"]["amount"] = مقدار
        db["charge"]["card"] = کارت

        save_database(db)

        await update.reply(
            "✅ شارژ ساختمان تنظیم شد.\n\n"
            f"📅 روز پرداخت: {روز} هر ماه\n"
            f"💰 مبلغ: {مبلغ(مقدار)} تومان\n"
            f"💳 شماره کارت:\n{کارت}"
        )

    except Exception:

        await update.reply(
            "❌ اطلاعات واردشده صحیح نیست."
        )


# =========================================================
# نمایش شارژ
# =========================================================

@app.on_update(
    filters.commands("شارژ")
)
async def نمایش_شارژ(client, update: Update):

    شارژ = db["charge"]

    await update.reply(
        "🏢 **اطلاعات شارژ ساختمان فدک**\n\n"
        f"📅 روز پرداخت: {شارژ['day']} هر ماه\n"
        f"💰 مبلغ: {مبلغ(شارژ['amount'])} تومان\n"
        f"💳 شماره کارت:\n"
        f"{شارژ['card']}\n\n"
        "📸 بعد از واریز، رسید را در PV بات ارسال کنید.\n"
        "👤 نام و نام خانوادگی خود را نیز ارسال کنید."
    )


# =========================================================
# ثبت هزینه
# =========================================================

@app.on_update(
    filters.commands("ثبت_هزینه")
)
async def ثبت_هزینه(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیر یا مالک می‌تواند هزینه ثبت کند."
        )

        return

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split(maxsplit=1)

    if len(بخش‌ها) < 2:

        await update.reply(
            "❌ روش استفاده:\n\n"
            "/ثبت_هزینه عنوان | مبلغ\n\n"
            "مثال:\n"
            "/ثبت_هزینه تعمیر آسانسور | 2500000"
        )

        return

    try:

        عنوان, مقدار = بخش‌ها[1].split("|", 1)

        عنوان = عنوان.strip()

        مقدار = int(
            عدد_فارسی_به_انگلیسی(
                مقدار.strip()
            )
        )

        هزینه = {
            "title": عنوان,
            "amount": مقدار,
            "created_by": user_id,
            "created_at": زمان()
        }

        db["expenses"].append(هزینه)

        save_database(db)

        await update.reply(
            "✅ هزینه با موفقیت ثبت شد.\n\n"
            f"📌 عنوان: {عنوان}\n"
            f"💰 مبلغ: {مبلغ(مقدار)} تومان"
        )

    except Exception:

        await update.reply(
            "❌ فرمت واردشده اشتباه است."
        )


# =========================================================
# لیست هزینه‌ها
# =========================================================

@app.on_update(
    filters.commands("هزینه‌ها")
)
async def هزینه_ها(client, update: Update):

    هزینه‌ها = db["expenses"]

    if not هزینه‌ها:

        await update.reply(
            "📋 هنوز هیچ هزینه‌ای ثبت نشده است."
        )

        return

    متن_خروجی = (
        "💰 **لیست هزینه‌های ساختمان فدک**\n\n"
    )

    جمع = 0

    for شماره, هزینه in enumerate(
        هزینه‌ها,
        1
    ):

        مقدار = int(
            هزینه["amount"]
        )

        جمع += مقدار

        متن_خروجی += (
            f"🔹 {شماره}. {هزینه['title']}\n"
            f"💵 {مبلغ(مقدار)} تومان\n"
            f"📅 {هزینه['created_at']}\n\n"
        )

    متن_خروجی += (
        "━━━━━━━━━━━━━━\n"
        f"💰 جمع کل: {مبلغ(جمع)} تومان"
    )

    await update.reply(متن_خروجی)


# =========================================================
# افزودن ساکن
# =========================================================

@app.on_update(
    filters.commands("افزودن_ساکن")
)
async def افزودن_ساکن(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند ساکن اضافه کنند."
        )

        return

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split(maxsplit=2)

    if len(بخش‌ها) < 3:

        await update.reply(
            "❌ روش استفاده:\n\n"
            "/افزودن_ساکن شناسه_کاربر نام و نام_خانوادگی"
        )

        return

    شناسه = بخش‌ها[1]

    نام = بخش‌ها[2]

    db["residents"][شناسه] = {
        "name": نام,
        "added_at": زمان()
    }

    save_database(db)

    await update.reply(
        "✅ ساکن ثبت شد.\n\n"
        f"👤 نام: {نام}\n"
        f"🆔 شناسه: {شناسه}"
    )


# =========================================================
# حذف ساکن
# =========================================================

@app.on_update(
    filters.commands("حذف_ساکن")
)
async def حذف_ساکن(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند ساکن حذف کنند."
        )

        return

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split(maxsplit=1)

    if len(بخش‌ها) < 2:

        await update.reply(
            "❌ روش استفاده:\n\n"
            "/حذف_ساکن شناسه_کاربر"
        )

        return

    شناسه = بخش‌ها[1].strip()

    if شناسه in db["residents"]:
        del db["residents"][شناسه]

    save_database(db)

    await update.reply(
        "✅ ساکن حذف شد."
    )


# =========================================================
# لیست ساکنین
# =========================================================

@app.on_update(
    filters.commands("ساکنین")
)
async def ساکنین(client, update: Update):

    if not db["residents"]:

        await update.reply(
            "👥 هنوز هیچ ساکنی ثبت نشده است."
        )

        return

    خروجی = "👥 **لیست ساکنین ساختمان فدک**\n\n"

    for شماره, (شناسه, اطلاعات) in enumerate(
        db["residents"].items(),
        1
    ):

        خروجی += (
            f"{شماره}. {اطلاعات['name']}\n"
            f"🆔 {شناسه}\n\n"
        )

    await update.reply(خروجی)


# =========================================================
# ثبت پرداخت
# =========================================================

@app.on_update(
    filters.commands("پرداخت"),
    filters.private
)
async def پرداخت(client, update: Update):

    user_id = شناسه_کاربر(update)

    متن_پیام = متن(update)

    بخش‌ها = متن_پیام.split(maxsplit=1)

    if len(بخش‌ها) < 2:

        await update.reply(
            "❌ نام و نام خانوادگی را وارد کنید.\n\n"
            "مثال:\n"
            "/پرداخت علی رضایی"
        )

        return

    نام = بخش‌ها[1].strip()

    ماه = ماه_فعلی()

    if ماه not in db["payments"]:
        db["payments"][ماه] = {}

    db["payments"][ماه][user_id] = {
        "name": نام,
        "status": "paid",
        "receipt": False,
        "registered_at": زمان()
    }

    save_database(db)

    await update.reply(
        "✅ پرداخت شما ثبت شد.\n\n"
        f"👤 نام: {نام}\n"
        f"📅 ماه: {ماه}\n\n"
        "📸 حالا رسید واریز را برای بات ارسال کنید."
    )


# =========================================================
# گزارش پرداخت‌ها
# =========================================================

def ساخت_گزارش():

    ماه = ماه_فعلی()

    پرداخت‌ها = db["payments"].get(
        ماه,
        {}
    )

    پرداخت_کرده = []
    پرداخت_نکرده = []

    for شناسه, اطلاعات in db["residents"].items():

        if شناسه in پرداخت‌ها:

            if پرداخت‌ها[شناسه].get("status") == "paid":

                پرداخت_کرده.append(
                    پرداخت‌ها[شناسه].get(
                        "name",
                        اطلاعات["name"]
                    )
                )

        else:

            پرداخت_نکرده.append(
                اطلاعات["name"]
            )

    خروجی = (
        "📊 **گزارش شارژ ساختمان فدک**\n\n"
        f"📅 ماه: {ماه}\n\n"
        f"✅ پرداخت کرده‌اند: {len(پرداخت_کرده)} نفر\n"
    )

    for نام in پرداخت_کرده:
        خروجی += f"• {نام}\n"

    خروجی += (
        f"\n❌ پرداخت نکرده‌اند: {len(پرداخت_نکرده)} نفر\n"
    )

    for نام in پرداخت_نکرده:
        خروجی += f"• {نام}\n"

    return خروجی


# =========================================================
# گزارش
# =========================================================

@app.on_update(
    filters.commands("گزارش")
)
async def گزارش(client, update: Update):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند گزارش را ببینند."
        )

        return

    await update.reply(
        ساخت_گزارش()
    )


# =========================================================
# پیام‌های عمومی گروه
# =========================================================

@app.on_update(
    filters.text,
    filters.group
)
async def پیام_گروه(client, update: Update):

    متن_پیام = متن(update)

    if متن_پیام in [
        "دستورات",
        "دستور",
        "راهنما"
    ]:

        await update.reply(
            دستورات
        )


# =========================================================
# زمان‌بندی ارسال شارژ
# =========================================================

async def زمانبندی_شارژ():

    آخرین_ارسال = None

    while True:

        try:

            امروز = datetime.now()

            روز_شارژ = int(
                db["charge"]["day"]
            )

            کلید = امروز.strftime("%Y-%m-%d")

            if امروز.day == روز_شارژ:

                if آخرین_ارسال != کلید:

                    پیام = (
                        "🏢 **شارژ ساختمان فدک**\n\n"
                        f"💰 مبلغ: "
                        f"{مبلغ(db['charge']['amount'])} تومان\n\n"
                        "💳 شماره کارت:\n"
                        f"{db['charge']['card']}\n\n"
                        "📸 بعد از واریز، رسید را در PV بات ارسال کنید.\n"
                        "👤 همراه رسید نام و نام خانوادگی خود را نیز بفرستید."
                    )

                    for شناسه_گروه, اطلاعات in db["groups"].items():

                        if not اطلاعات.get("active"):
                            continue

                        try:

                            await app.send_message(
                                شناسه_گروه,
                                پیام
                            )

                        except Exception as خطا:

                            print(
                                "خطا در ارسال شارژ:",
                                خطا
                            )

                    آخرین_ارسال = کلید

            await asyncio.sleep(3600)

        except Exception as خطا:

            print(
                "خطا در زمان‌بندی شارژ:",
                خطا
            )

            await asyncio.sleep(3600)


# =========================================================
# گزارش روز پنجم
# =========================================================

async def گزارش_روز_پنجم():

    آخرین_گزارش = None

    while True:

        try:

            امروز = datetime.now()

            کلید = امروز.strftime("%Y-%m-%d")

            if امروز.day == 5:

                if آخرین_گزارش != کلید:

                    گزارش_متن = ساخت_گزارش()

                    مدیران = set()

                    if db["owner_id"]:
                        مدیران.add(
                            str(db["owner_id"])
                        )

                    for مدیر in db["admins"]:
                        مدیران.add(
                            str(مدیر)
                        )

                    for مدیر in مدیران:

                        try:

                            await app.send_message(
                                مدیر,
                                گزارش_متن
                            )

                        except Exception as خطا:

                            print(
                                "خطا در ارسال گزارش:",
                                خطا
                            )

                    آخرین_گزارش = کلید

            await asyncio.sleep(3600)

        except Exception as خطا:

            print(
                "خطا در گزارش:",
                خطا
            )

            await asyncio.sleep(3600)


# =========================================================
# اجرای برنامه
# =========================================================

async def اجرای_زمانبندی‌ها():

    await asyncio.gather(
        زمانبندی_شارژ(),
        گزارش_روز_پنجم()
    )


if __name__ == "__main__":

    print("===================================")
    print("🏢 بات ساختمان فدک")
    print("🚀 در حال اجرا...")
    print("===================================")

    حلقه = asyncio.get_event_loop()

    حلقه.create_task(
        اجرای_زمانبندی‌ها()
    )

    app.run()
