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

DATABASE_FILE = "database.json"

app = BotClient(TOKEN)


# =========================================================
# دیتابیس پیش‌فرض
# =========================================================

DATABASE_DEFAULT = {
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


# =========================================================
# دیتابیس
# =========================================================

def load_database():

    if not os.path.exists(DATABASE_FILE):

        save_database(DATABASE_DEFAULT)

        return DATABASE_DEFAULT.copy()

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        for key, value in DATABASE_DEFAULT.items():

            if key not in data:

                data[key] = value

        return data

    except Exception:

        save_database(DATABASE_DEFAULT)

        return DATABASE_DEFAULT.copy()


def save_database(data):

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


db = load_database()


# =========================================================
# ابزارها
# =========================================================

def زمان():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def ماه_فعلی():

    return datetime.now().strftime(
        "%Y-%m"
    )


def شناسه_کاربر(update):

    try:

        return str(
            update.new_message.sender_id
        )

    except Exception:

        return None


def متن(update):

    try:

        return (
            update.new_message.text or ""
        ).strip()

    except Exception:

        return ""


def عدد_فارسی(value):

    if value is None:
        return ""

    return str(value).translate(
        str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹",
            "0123456789"
        )
    )


def پول(value):

    try:

        return f"{int(value):,}"

    except Exception:

        return str(value)


def مدیر_است(user_id):

    if not user_id:
        return False

    user_id = str(user_id)

    if str(db["owner_id"]) == user_id:
        return True

    return user_id in [
        str(x)
        for x in db["admins"]
    ]


def مالک_است(user_id):

    if not user_id:
        return False

    return str(
        db["owner_id"]
    ) == str(user_id)


# =========================================================
# راهنمای بات
# =========================================================

راهنما = """
🏢 بات ساختمان فدک

━━━━━━━━━━━━━━━━━━

📋 دستورات عمومی:

دستورات
نمایش لیست دستورات

شارژ
نمایش مبلغ و اطلاعات شارژ

هزینه‌ها
نمایش تمام هزینه‌های ساختمان

پرداخت
ثبت پرداخت شارژ

━━━━━━━━━━━━━━━━━━

👑 دستورات مدیریتی:

مدیر
ثبت اولین مدیر و مالک بات

افزودن مدیر
افزودن مدیر جدید

حذف مدیر
حذف مدیر

تنظیم شارژ
تنظیم روز، مبلغ و شماره کارت

ثبت هزینه
ثبت هزینه ساختمان

ساکنین
نمایش لیست ساکنین

افزودن ساکن
ثبت ساکن جدید

حذف ساکن
حذف ساکن

گزارش
گزارش پرداخت و عدم پرداخت

━━━━━━━━━━━━━━━━━━

⚡ مدیریت سریع:

روی پیام شخص موردنظر ریپلای کنید و بنویسید:

ادمین میتونه

━━━━━━━━━━━━━━━━━━

📸 پرداخت شارژ:

رسید واریز را برای بات در PV ارسال کنید.

همراه رسید:
نام و نام خانوادگی

را نیز ارسال کنید.
"""


# =========================================================
# فعال کردن بات در گروه
# =========================================================

@app.on_update(
    filters.text("فعال"),
    filters.group
)
async def فعال(client, update: Update):

    chat_id = str(
        update.chat_id
    )

    db["groups"][chat_id] = {
        "active": True,
        "activated_at": زمان()
    }

    save_database(db)

    await update.reply(
        "✅ بات ساختمان فدک فعال شد.\n\n"
        + راهنما
    )


# =========================================================
# دستورات عمومی بدون /
# =========================================================

@app.on_update(
    filters.text,
    filters.group
)
async def دستورات_گروه(
    client,
    update: Update
):

    message = متن(update)

    if not message:
        return

    # -----------------------------------------
    # دستورات عمومی
    # -----------------------------------------

    if message == "دستورات":

        await update.reply(
            راهنما
        )

        return

    if message == "راهنما":

        await update.reply(
            راهنما
        )

        return

    if message == "شارژ":

        await نمایش_شارژ(
            client,
            update
        )

        return

    if message == "هزینه‌ها":

        await نمایش_هزینه‌ها(
            client,
            update
        )

        return

    if message == "ساکنین":

        await نمایش_ساکنین(
            client,
            update
        )

        return

    if message == "گزارش":

        await نمایش_گزارش(
            client,
            update
        )

        return

    # -----------------------------------------
    # مدیر
    # -----------------------------------------

    if message == "مدیر":

        await ثبت_مدیر(
            client,
            update
        )

        return

    # -----------------------------------------
    # افزودن مدیر
    # -----------------------------------------

    if message.startswith(
        "افزودن مدیر"
    ):

        await افزودن_مدیر(
            client,
            update
        )

        return

    # -----------------------------------------
    # حذف مدیر
    # -----------------------------------------

    if message.startswith(
        "حذف مدیر"
    ):

        await حذف_مدیر(
            client,
            update
        )

        return

    # -----------------------------------------
    # تنظیم شارژ
    # -----------------------------------------

    if message.startswith(
        "تنظیم شارژ"
    ):

        await تنظیم_شارژ(
            client,
            update
        )

        return

    # -----------------------------------------
    # ثبت هزینه
    # -----------------------------------------

    if message.startswith(
        "ثبت هزینه"
    ):

        await ثبت_هزینه(
            client,
            update
        )

        return

    # -----------------------------------------
    # افزودن ساکن
    # -----------------------------------------

    if message.startswith(
        "افزودن ساکن"
    ):

        await افزودن_ساکن(
            client,
            update
        )

        return

    # -----------------------------------------
    # حذف ساکن
    # -----------------------------------------

    if message.startswith(
        "حذف ساکن"
    ):

        await حذف_ساکن(
            client,
            update
        )

        return

    # -----------------------------------------
    # پرداخت
    # -----------------------------------------

    if message.startswith(
        "پرداخت"
    ):

        await ثبت_پرداخت(
            client,
            update
        )

        return

    # -----------------------------------------
    # ادمین با ریپلای
    # -----------------------------------------

    if message == "ادمین میتونه":

        await ادمین_با_ریپلای(
            client,
            update
        )

        return


# =========================================================
# ثبت مالک
# =========================================================

async def ثبت_مدیر(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not user_id:
        return

    if db["owner_id"] is None:

        db["owner_id"] = user_id

        if user_id not in db["admins"]:

            db["admins"].append(
                user_id
            )

        save_database(db)

        await update.reply(
            "👑 مالک بات ثبت شد.\n\n"
            "شما مالک اصلی بات ساختمان فدک هستید."
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

async def افزودن_مدیر(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مالک_است(user_id):

        await update.reply(
            "❌ فقط مالک اصلی می‌تواند مدیر اضافه کند."
        )

        return

    message = متن(update)

    parts = message.split(
        maxsplit=2
    )

    if len(parts) < 3:

        await update.reply(
            "❌ روش صحیح:\n\n"
            "افزودن مدیر شناسه_کاربر"
        )

        return

    target = parts[2].strip()

    if target not in db["admins"]:

        db["admins"].append(
            target
        )

        save_database(db)

    await update.reply(
        "✅ مدیر جدید اضافه شد.\n\n"
        f"شناسه: {target}"
    )


# =========================================================
# حذف مدیر
# =========================================================

async def حذف_مدیر(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مالک_است(user_id):

        await update.reply(
            "❌ فقط مالک اصلی می‌تواند مدیر حذف کند."
        )

        return

    message = متن(update)

    parts = message.split(
        maxsplit=2
    )

    if len(parts) < 3:

        await update.reply(
            "❌ روش صحیح:\n\n"
            "حذف مدیر شناسه_کاربر"
        )

        return

    target = parts[2].strip()

    if target == str(
        db["owner_id"]
    ):

        await update.reply(
            "❌ مالک اصلی را نمی‌توان حذف کرد."
        )

        return

    if target in db["admins"]:

        db["admins"].remove(
            target
        )

        save_database(db)

        await update.reply(
            "✅ مدیر حذف شد."
        )

    else:

        await update.reply(
            "❌ این کاربر مدیر نیست."
        )


# =========================================================
# تنظیم شارژ
# =========================================================

async def تنظیم_شارژ(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند شارژ را تنظیم کنند."
        )

        return

    message = متن(update)

    parts = message.split()

    if len(parts) < 4:

        await update.reply(
            "❌ روش صحیح:\n\n"
            "تنظیم شارژ روز مبلغ شماره_کارت\n\n"
            "مثال:\n"
            "تنظیم شارژ 1 500000 6037991234567890"
        )

        return

    try:

        day = int(
            عدد_فارسی(
                parts[2]
            )
        )

        amount = int(
            عدد_فارسی(
                parts[3]
            )
        )

        card = عدد_فارسی(
            parts[4]
        )

        if day < 1 or day > 31:

            raise ValueError

        db["charge"]["day"] = day

        db["charge"]["amount"] = amount

        db["charge"]["card"] = card

        save_database(db)

        await update.reply(
            "✅ شارژ تنظیم شد.\n\n"
            f"📅 روز: {day} هر ماه\n"
            f"💰 مبلغ: {پول(amount)} تومان\n"
            f"💳 کارت:\n{card}"
        )

    except Exception:

        await update.reply(
            "❌ اطلاعات واردشده صحیح نیست."
        )


# =========================================================
# نمایش شارژ
# =========================================================

async def نمایش_شارژ(
    client,
    update
):

    charge = db["charge"]

    await update.reply(
        "🏢 اطلاعات شارژ ساختمان فدک\n\n"
        f"📅 روز پرداخت: {charge['day']} هر ماه\n"
        f"💰 مبلغ: {پول(charge['amount'])} تومان\n"
        f"💳 شماره کارت:\n"
        f"{charge['card']}\n\n"
        "📸 پس از واریز رسید را در PV بات ارسال کنید.\n"
        "👤 نام و نام خانوادگی خود را نیز بنویسید."
    )


# =========================================================
# ثبت هزینه
# =========================================================

async def ثبت_هزینه(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیر یا مالک می‌تواند هزینه ثبت کند."
        )

        return

    message = متن(update)

    if "|" not in message:

        await update.reply(
            "❌ روش صحیح:\n\n"
            "ثبت هزینه عنوان | مبلغ\n\n"
            "مثال:\n"
            "ثبت هزینه تعمیر آسانسور | 2500000"
        )

        return

    try:

        data = message[
            len("ثبت هزینه"):
        ].strip()

        title, amount = data.split(
            "|",
            1
        )

        title = title.strip()

        amount = int(
            عدد_فارسی(
                amount.strip()
            )
        )

        expense = {
            "title": title,
            "amount": amount,
            "created_by": user_id,
            "created_at": زمان()
        }

        db["expenses"].append(
            expense
        )

        save_database(db)

        await update.reply(
            "✅ هزینه ثبت شد.\n\n"
            f"📌 عنوان: {title}\n"
            f"💰 مبلغ: {پول(amount)} تومان"
        )

    except Exception:

        await update.reply(
            "❌ اطلاعات هزینه صحیح نیست."
        )


# =========================================================
# نمایش هزینه‌ها
# =========================================================

async def نمایش_هزینه‌ها(
    client,
    update
):

    expenses = db["expenses"]

    if not expenses:

        await update.reply(
            "📋 هنوز هیچ هزینه‌ای ثبت نشده است."
        )

        return

    result = (
        "💰 هزینه‌های ساختمان فدک\n\n"
    )

    total = 0

    for index, expense in enumerate(
        expenses,
        1
    ):

        amount = int(
            expense["amount"]
        )

        total += amount

        result += (
            f"🔹 {index}. {expense['title']}\n"
            f"💵 {پول(amount)} تومان\n"
            f"📅 {expense['created_at']}\n\n"
        )

    result += (
        "━━━━━━━━━━━━━━\n"
        f"💰 جمع کل: {پول(total)} تومان"
    )

    await update.reply(
        result
    )


# =========================================================
# افزودن ساکن
# =========================================================

async def افزودن_ساکن(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند ساکن اضافه کنند."
        )

        return

    message = متن(update)

    parts = message.split(
        maxsplit=2
    )

    if len(parts) < 3:

        await update.reply(
            "❌ روش صحیح:\n\n"
            "افزودن ساکن شناسه نام و نام خانوادگی"
        )

        return

    target = parts[2].split(
        maxsplit=1
    )

    if len(target) < 2:

        await update.reply(
            "❌ نام و نام خانوادگی را کامل وارد کنید."
        )

        return

    # چون فرمت ساده است، برای شناسه و نام بهتر است:
    # افزودن ساکن 123456 علی رضایی

    pieces = message.split(
        maxsplit=3
    )

    if len(pieces) < 4:

        await update.reply(
            "❌ مثال:\n\n"
            "افزودن ساکن 123456 علی رضایی"
        )

        return

    resident_id = pieces[2]

    name = pieces[3]

    db["residents"][
        resident_id
    ] = {
        "name": name,
        "added_at": زمان()
    }

    save_database(db)

    await update.reply(
        "✅ ساکن ثبت شد.\n\n"
        f"👤 نام: {name}\n"
        f"🆔 شناسه: {resident_id}"
    )


# =========================================================
# حذف ساکن
# =========================================================

async def حذف_ساکن(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مدیر_است(user_id):

        await update.reply(
            "❌ فقط مدیران می‌توانند ساکن حذف کنند."
        )

        return

    parts = متن(update).split()

    if len(parts) < 3:

        await update.reply(
            "❌ روش صحیح:\n\n"
            "حذف ساکن شناسه_کاربر"
        )

        return

    target = parts[2]

    if target in db["residents"]:

        del db["residents"][target]

        save_database(db)

        await update.reply(
            "✅ ساکن حذف شد."
        )

    else:

        await update.reply(
            "❌ این ساکن پیدا نشد."
        )


# =========================================================
# نمایش ساکنین
# =========================================================

async def نمایش_ساکنین(
    client,
    update
):

    if not db["residents"]:

        await update.reply(
            "👥 هنوز ساکنی ثبت نشده است."
        )

        return

    result = (
        "👥 لیست ساکنین ساختمان فدک\n\n"
    )

    for index, (
        user_id,
        info
    ) in enumerate(
        db["residents"].items(),
        1
    ):

        result += (
            f"{index}. {info['name']}\n"
            f"🆔 {user_id}\n\n"
        )

    await update.reply(
        result
    )


# =========================================================
# ثبت پرداخت
# =========================================================

async def ثبت_پرداخت(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    message = متن(update)

    name = message[
        len("پرداخت"):
    ].strip()

    if not name:

        await update.reply(
            "❌ نام و نام خانوادگی را بنویسید.\n\n"
            "مثال:\n"
            "پرداخت علی رضایی"
        )

        return

    month = ماه_فعلی()

    if month not in db["payments"]:

        db["payments"][month] = {}

    db["payments"][month][
        user_id
    ] = {
        "name": name,
        "status": "paid",
        "receipt": False,
        "registered_at": زمان()
    }

    save_database(db)

    await update.reply(
        "✅ پرداخت شما ثبت شد.\n\n"
        f"👤 نام: {name}\n"
        f"📅 ماه: {month}\n\n"
        "📸 لطفاً رسید واریز را نیز برای بات ارسال کنید."
    )


# =========================================================
# ساخت گزارش
# =========================================================

def ساخت_گزارش():

    month = ماه_فعلی()

    payments = db[
        "payments"
    ].get(
        month,
        {}
    )

    paid = []

    unpaid = []

    for resident_id, info in db[
        "residents"
    ].items():

        if resident_id in payments:

            if payments[
                resident_id
            ].get("status") == "paid":

                paid.append(
                    payments[
                        resident_id
                    ].get(
                        "name",
                        info["name"]
                    )
                )

        else:

            unpaid.append(
                info["name"]
            )

    result = (
        "📊 گزارش شارژ ساختمان فدک\n\n"
        f"📅 ماه: {month}\n\n"
        f"✅ پرداخت کرده‌اند: {len(paid)} نفر\n"
    )

    if paid:

        for name in paid:

            result += (
                f"• {name}\n"
            )

    result += (
        f"\n❌ پرداخت نکرده‌اند: "
        f"{len(unpaid)} نفر\n"
    )

    if unpaid:

        for name in unpaid:

            result += (
                f"• {name}\n"
            )

    return result


# =========================================================
# گزارش
# =========================================================

async def نمایش_گزارش(
    client,
    update
):

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
# ادمین با ریپلای
# =========================================================

async def ادمین_با_ریپلای(
    client,
    update
):

    user_id = شناسه_کاربر(update)

    if not مالک_است(user_id):

        await update.reply(
            "❌ فقط مالک اصلی می‌تواند مدیر اضافه کند."
        )

        return

    message = update.new_message

    reply_id = getattr(
        message,
        "reply_to_message_id",
        None
    )

    if not reply_id:

        await update.reply(
            "❌ باید روی پیام شخص موردنظر ریپلای کنید."
        )

        return

    await update.reply(
        "⚠️ پیام ریپلای‌شده پیدا شد، "
        "اما برای گرفتن شناسه صاحب آن پیام باید "
        "از متد واکشی پیام نسخه نصب‌شده Rubpy استفاده شود."
    )


# =========================================================
# زمان‌بندی شارژ
# =========================================================

async def زمانبندی_شارژ():

    last_sent = None

    while True:

        try:

            now = datetime.now()

            day = int(
                db["charge"]["day"]
            )

            today = now.strftime(
                "%Y-%m-%d"
            )

            if now.day == day:

                if last_sent != today:

                    message = (
                        "🏢 شارژ ساختمان فدک\n\n"
                        f"💰 مبلغ: "
                        f"{پول(db['charge']['amount'])} تومان\n\n"
                        "💳 شماره کارت:\n"
                        f"{db['charge']['card']}\n\n"
                        "📸 پس از واریز، رسید را "
                        "در PV بات ارسال کنید.\n"
                        "👤 نام و نام خانوادگی خود را نیز بفرستید."
                    )

                    for group_id, info in db[
                        "groups"
                    ].items():

                        if not info.get(
                            "active"
                        ):
                            continue

                        try:

                            await app.send_message(
                                group_id,
                                message
                            )

                        except Exception as error:

                            print(
                                "خطای ارسال شارژ:",
                                error
                            )

                    last_sent = today

            await asyncio.sleep(
                3600
            )

        except Exception as error:

            print(
                "خطای زمان‌بندی:",
                error
            )

            await asyncio.sleep(
                3600
            )


# =========================================================
# گزارش روز پنجم
# =========================================================

async def گزارش_روز_پنجم():

    last_report = None

    while True:

        try:

            now = datetime.now()

            today = now.strftime(
                "%Y-%m-%d"
            )

            if now.day == 5:

                if last_report != today:

                    report = ساخت_گزارش()

                    admins = set()

                    if db["owner_id"]:

                        admins.add(
                            str(
                                db["owner_id"]
                            )
                        )

                    for admin in db[
                        "admins"
                    ]:

                        admins.add(
                            str(admin)
                        )

                    for admin in admins:

                        try:

                            await app.send_message(
                                admin,
                                report
                            )

                        except Exception as error:

                            print(
                                "خطای گزارش:",
                                error
                            )

                    last_report = today

            await asyncio.sleep(
                3600
            )

        except Exception as error:

            print(
                "خطای گزارش روز پنجم:",
                error
            )

            await asyncio.sleep(
                3600
            )


# =========================================================
# اجرای زمان‌بندی‌ها
# =========================================================

async def اجرای_زمانبندی():

    await asyncio.gather(
        زمانبندی_شارژ(),
        گزارش_روز_پنجم()
    )


# =========================================================
# اجرای بات
# =========================================================

if __name__ == "__main__":

    print(
        "================================="
    )

    print(
        "🏢 بات ساختمان فدک"
    )

    print(
        "🚀 بات در حال اجراست..."
    )

    print(
        "================================="
    )

    loop = asyncio.get_event_loop()

    loop.create_task(
        اجرای_زمانبندی()
    )

    app.run()
