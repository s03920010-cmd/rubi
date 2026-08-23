import asyncio
import json
import os
from datetime import datetime


# ============================================================
# Rubpy
# ============================================================

from rubpy import BotClient
from rubpy import filters


# ============================================================
# تنظیمات
# ============================================================

BOT_TOKEN = "CCFDJD0NTXGROTMRYNTFWCULTGQFIMGSSUQXHXJFGYBVXYAJWJRTNMSKUGAOLOJT"

OWNER_USERNAME = "radvinhha"

DATABASE_FILE = "database.json"


# ============================================================
# ساخت Bot
# ============================================================

bot = BotClient(
    token=BOT_TOKEN,
    rate_limit=0.5
)


# ============================================================
# دیتابیس
# ============================================================

def default_database():
    return {
        "bot": {
            "name": "بات ساختمان فدک",
            "active": True
        },

        "owner": {
            "username": OWNER_USERNAME,
            "user_id": None
        },

        "admins": [],

        "users": [],

        "groups": [],

        "bank_cards": [],

        "expenses": [],

        "reminders": []
    }


def create_database():
    if not os.path.exists(DATABASE_FILE):

        data = default_database()

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


def load_database():

    create_database()

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        data = default_database()

        save_database(data)

        return data


def save_database(data):

    temp_file = DATABASE_FILE + ".tmp"

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    os.replace(
        temp_file,
        DATABASE_FILE
    )


# ============================================================
# ابزارها
# ============================================================

def normalize(text):

    if not text:
        return ""

    return (
        str(text)
        .strip()
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("\u200c", " ")
    )


def get_message(update):

    return getattr(
        update,
        "new_message",
        None
    )


def get_text(update):

    message = get_message(update)

    if not message:
        return ""

    return normalize(
        getattr(
            message,
            "text",
            ""
        )
    )


def get_sender_id(update):

    message = get_message(update)

    if not message:
        return None

    return getattr(
        message,
        "sender_id",
        None
    )


def get_chat_id(update):

    return getattr(
        update,
        "chat_id",
        None
    )


def format_money(amount):

    try:
        return f"{int(amount):,}"
    except Exception:
        return str(amount)


# ============================================================
# کاربر
# ============================================================

def save_user(update):

    user_id = get_sender_id(update)

    if not user_id:
        return

    data = load_database()

    if user_id not in data["users"]:

        data["users"].append(user_id)

        save_database(data)


# ============================================================
# مالک
# ============================================================

def is_owner(update):

    data = load_database()

    sender_id = get_sender_id(update)

    owner_id = data["owner"].get("user_id")

    if owner_id:

        return str(sender_id) == str(owner_id)

    return False


def register_owner(update):

    sender_id = get_sender_id(update)

    if not sender_id:
        return False

    data = load_database()

    owner_id = data["owner"].get("user_id")

    if owner_id is None:

        data["owner"]["user_id"] = sender_id

        save_database(data)

        return True

    return str(owner_id) == str(sender_id)


# ============================================================
# ادمین
# ============================================================

def is_admin(update):

    if is_owner(update):
        return True

    sender_id = get_sender_id(update)

    if not sender_id:
        return False

    data = load_database()

    return any(
        str(admin["user_id"]) == str(sender_id)
        for admin in data["admins"]
    )


def add_admin(user_id, username=""):

    data = load_database()

    for admin in data["admins"]:

        if str(admin["user_id"]) == str(user_id):
            return False

    data["admins"].append({
        "user_id": user_id,
        "username": username
    })

    save_database(data)

    return True


# ============================================================
# گروه
# ============================================================

def register_group(update):

    chat_id = get_chat_id(update)

    if not chat_id:
        return

    data = load_database()

    if chat_id not in data["groups"]:

        data["groups"].append(chat_id)

        save_database(data)


# ============================================================
# منوی اصلی
# ============================================================

def main_menu():

    return (
        "🏢 بات ساختمان فدک\n\n"

        "درود 👋\n\n"

        "این بات مخصوص ساختمان فدک است.\n\n"

        "📌 امکانات:\n"
        "💰 مشاهده هزینه‌های ساختمان\n"
        "💳 مشاهده شماره کارت\n"
        "🔔 یادآوری‌ها\n\n"

        "برای مشاهده کل هزینه‌های ساختمان:\n"
        "🔹 هزینه\n\n"

        "دستورات مدیریت:\n"
        "⚙️ مدیریت"
    )


def admin_menu():

    return (
        "⚙️ پنل مدیریت ساختمان فدک\n\n"

        "دستورات:\n\n"

        "👤 افزودن ادمین\n"
        "فرمت:\n"
        "افزودن ادمین USER_ID\n\n"

        "💳 افزودن شماره کارت\n"
        "فرمت:\n"
        "افزودن شماره کارت\n"
        "عنوان\n"
        "شماره کارت\n\n"

        "💰 افزودن هزینه\n"
        "فرمت:\n"
        "افزودن هزینه\n"
        "عنوان\n"
        "مبلغ\n"
        "توضیحات\n\n"

        "🔔 افزودن یادآوری\n"
        "فرمت:\n"
        "افزودن یادآوری\n"
        "روز\n"
        "عنوان\n"
        "متن\n\n"

        "🟢 فعال سازی\n"
        "🔴 غیرفعال سازی"
    )


# ============================================================
# START
# ============================================================

@bot.on_update(
    filters.private,
    filters.commands("start")
)
async def start_handler(client, update):

    save_user(update)

    # اولین /start مالک را ثبت می‌کند
    register_owner(update)

    data = load_database()

    text = (
        "🏢 **بات ساختمان فدک**\n\n"

        "درود 👋\n\n"

        "این بات برای ساختمان فدک ساخته شده است.\n\n"

        "💰 برای مشاهده کل هزینه‌های ساختمان:\n"
        "**هزینه**\n\n"

        "💳 برای مشاهده شماره کارت:\n"
        "**شماره کارت**\n\n"

        "🔔 یادآوری‌های ساختمان نیز توسط بات ارسال می‌شوند.\n"
    )

    if data["bot"]["active"]:

        text += "\n🟢 وضعیت: فعال"

    else:

        text += "\n🔴 وضعیت: غیرفعال"

    if is_admin(update):

        text += (
            "\n\n⚙️ برای ورود به مدیریت:\n"
            "**مدیریت**"
        )

    await update.reply(text)


# ============================================================
# پیام‌های خصوصی
# ============================================================

@bot.on_update(filters.private)
async def private_handler(client, update):

    save_user(update)

    text = get_text(update)

    if not text:
        return

    # --------------------------------------------------------
    # مدیریت
    # --------------------------------------------------------

    if text == "مدیریت":

        if not is_admin(update):

            await update.reply(
                "⛔ شما اجازه دسترسی به پنل مدیریت را ندارید."
            )

            return

        await update.reply(
            admin_menu()
        )

        return

    # --------------------------------------------------------
    # فعال سازی
    # --------------------------------------------------------

    if text == "فعال سازی":

        if not is_admin(update):
            return

        data = load_database()

        data["bot"]["active"] = True

        save_database(data)

        await update.reply(
            "🟢 **بات ساختمان فدک فعال شد.**\n\n"
            "این بات برای ساختمان فدک است.\n\n"
            "برای مشاهده کل هزینه‌های ساختمان:\n"
            "**هزینه**"
        )

        return

    # --------------------------------------------------------
    # غیرفعال سازی
    # --------------------------------------------------------

    if text == "غیرفعال سازی":

        if not is_admin(update):
            return

        data = load_database()

        data["bot"]["active"] = False

        save_database(data)

        await update.reply(
            "🔴 بات ساختمان فدک غیرفعال شد."
        )

        return

    # --------------------------------------------------------
    # افزودن ادمین
    # --------------------------------------------------------

    if text.startswith("افزودن ادمین"):

        if not is_owner(update):

            await update.reply(
                "⛔ فقط مالک اصلی می‌تواند ادمین اضافه کند."
            )

            return

        parts = text.split()

        if len(parts) < 3:

            await update.reply(
                "❌ فرمت صحیح:\n\n"
                "افزودن ادمین USER_ID"
            )

            return

        user_id = parts[2]

        if add_admin(user_id):

            await update.reply(
                "✅ ادمین با موفقیت اضافه شد."
            )

        else:

            await update.reply(
                "⚠️ این کاربر از قبل ادمین است."
            )

        return

    # --------------------------------------------------------
    # افزودن شماره کارت
    # --------------------------------------------------------

    if text.startswith("افزودن شماره کارت"):

        if not is_admin(update):
            return

        lines = text.splitlines()

        if len(lines) < 3:

            await update.reply(
                "❌ فرمت صحیح:\n\n"
                "افزودن شماره کارت\n"
                "عنوان\n"
                "شماره کارت"
            )

            return

        title = lines[1].strip()
        card_number = lines[2].strip()

        data = load_database()

        data["bank_cards"].append({

            "title": title,

            "card_number": card_number,

            "created_at":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        })

        save_database(data)

        await update.reply(
            "✅ شماره کارت ثبت شد."
        )

        return

    # --------------------------------------------------------
    # شماره کارت
    # --------------------------------------------------------

    if text in (
        "شماره کارت",
        "شماره کارت ها",
        "شماره کارت‌ها"
    ):

        data = load_database()

        cards = data.get(
            "bank_cards",
            []
        )

        if not cards:

            await update.reply(
                "💳 هنوز شماره کارتی ثبت نشده است."
            )

            return

        result = [
            "💳 **شماره کارت‌های ساختمان فدک**\n"
        ]

        for card in cards:

            result.append(
                f"🔹 {card['title']}\n"
                f"💳 `{card['card_number']}`\n"
            )

        await update.reply(
            "\n".join(result)
        )

        return

    # --------------------------------------------------------
    # افزودن هزینه
    # --------------------------------------------------------

    if text.startswith("افزودن هزینه"):

        if not is_admin(update):
            return

        lines = text.splitlines()

        if len(lines) < 3:

            await update.reply(
                "❌ فرمت صحیح:\n\n"
                "افزودن هزینه\n"
                "عنوان\n"
                "مبلغ\n"
                "توضیحات"
            )

            return

        title = lines[1].strip()

        try:

            amount = int(
                lines[2]
                .replace(",", "")
                .replace("٬", "")
                .replace("تومان", "")
                .strip()
            )

        except ValueError:

            await update.reply(
                "❌ مبلغ واردشده صحیح نیست."
            )

            return

        description = ""

        if len(lines) >= 4:

            description = "\n".join(
                lines[3:]
            ).strip()

        data = load_database()

        data["expenses"].append({

            "title": title,

            "amount": amount,

            "description": description,

            "date":
                datetime.now().strftime(
                    "%Y-%m-%d"
                ),

            "added_by":
                get_sender_id(update)
        })

        save_database(data)

        await update.reply(
            "✅ هزینه با موفقیت ثبت شد."
        )

        return

    # --------------------------------------------------------
    # افزودن یادآوری
    # --------------------------------------------------------

    if text.startswith("افزودن یادآوری"):

        if not is_admin(update):
            return

        lines = text.splitlines()

        if len(lines) < 4:

            await update.reply(
                "❌ فرمت صحیح:\n\n"
                "افزودن یادآوری\n"
                "روز\n"
                "عنوان\n"
                "متن"
            )

            return

        day = lines[1].strip()
        title = lines[2].strip()

        reminder_text = "\n".join(
            lines[3:]
        ).strip()

        data = load_database()

        data["reminders"].append({

            "day": day,

            "title": title,

            "text": reminder_text,

            "last_sent": None
        })

        save_database(data)

        await update.reply(
            f"🔔 یادآوری روز {day} ثبت شد."
        )

        return

    # --------------------------------------------------------
    # هزینه
    # --------------------------------------------------------

    if text in (
        "هزینه",
        "هزینه ها",
        "هزینه‌ها",
        "هزینه کل"
    ):

        data = load_database()

        expenses = data.get(
            "expenses",
            []
        )

        if not expenses:

            await update.reply(
                "🏢 **ساختمان فدک**\n\n"
                "💰 هنوز هیچ هزینه‌ای ثبت نشده است."
            )

            return

        total = 0

        result = [
            "🏢 **ساختمان فدک**\n",
            "💰 **هزینه‌ها:**\n"
        ]

        for expense in expenses:

            amount = int(
                expense.get(
                    "amount",
                    0
                )
            )

            total += amount

            result.append(
                f"🔹 {expense.get('title', '-')}\n"
                f"💵 {format_money(amount)} تومان\n"
                f"📅 {expense.get('date', '-')}\n"
            )

        result.append(
            "━━━━━━━━━━━━\n"
            f"💰 **کل هزینه‌ها: "
            f"{format_money(total)} تومان**"
        )

        await update.reply(
            "\n".join(result)
        )

        return


# ============================================================
# گروه
# ============================================================

@bot.on_update(filters.group)
async def group_handler(client, update):

    register_group(update)

    text = get_text(update)

    if not text:
        return

    data = load_database()

    # --------------------------------------------------------
    # اگر بات غیرفعال باشد
    # --------------------------------------------------------

    if not data["bot"]["active"]:
        return

    # --------------------------------------------------------
    # هزینه
    # --------------------------------------------------------

    if text in (
        "هزینه",
        "هزینه ها",
        "هزینه‌ها",
        "هزینه کل",
        "هزینه های ساختمان",
        "هزینه‌های ساختمان"
    ):

        expenses = data.get(
            "expenses",
            []
        )

        if not expenses:

            await update.reply(
                "🏢 ساختمان فدک\n\n"
                "💰 هنوز هیچ هزینه‌ای ثبت نشده است."
            )

            return

        total = 0

        result = [
            "🏢 **ساختمان فدک**\n",
            "💰 **گزارش هزینه‌ها**\n"
        ]

        for expense in expenses:

            amount = int(
                expense.get(
                    "amount",
                    0
                )
            )

            total += amount

            result.append(
                f"🔹 {expense.get('title', '-')}\n"
                f"💵 {format_money(amount)} تومان\n"
                f"📅 {expense.get('date', '-')}\n"
            )

        result.append(
            "━━━━━━━━━━━━\n"
            f"💰 **کل هزینه‌ها: "
            f"{format_money(total)} تومان**"
        )

        await update.reply(
            "\n".join(result)
        )

        return

    # --------------------------------------------------------
    # شماره کارت
    # --------------------------------------------------------

    if text in (
        "شماره کارت",
        "شماره کارت ها",
        "شماره کارت‌ها"
    ):

        cards = data.get(
            "bank_cards",
            []
        )

        if not cards:

            await update.reply(
                "💳 هنوز شماره کارتی ثبت نشده است."
            )

            return

        result = [
            "💳 **شماره کارت ساختمان فدک**\n"
        ]

        for card in cards:

            result.append(
                f"🔹 {card['title']}\n"
                f"💳 `{card['card_number']}`\n"
            )

        await update.reply(
            "\n".join(result)
        )

        return


# ============================================================
# سیستم یادآوری
# ============================================================

async def reminder_loop():

    while True:

        try:

            data = load_database()

            if not data["bot"]["active"]:

                await asyncio.sleep(60)

                continue

            now = datetime.now()

            current_day = str(
                now.day
            )

            today = now.strftime(
                "%Y-%m-%d"
            )

            changed = False

            for reminder in data.get(
                "reminders",
                []
            ):

                if str(
                    reminder.get("day")
                ) != current_day:

                    continue

                if reminder.get(
                    "last_sent"
                ) == today:

                    continue

                message = (
                    "🔔 **یادآوری ساختمان فدک**\n\n"
                    f"📌 {reminder.get('title', '')}\n\n"
                    f"{reminder.get('text', '')}"
                )

                # ارسال به تمام گروه‌هایی که
                # بات در آن‌ها پیام دیده است
                for chat_id in data.get(
                    "groups",
                    []
                ):

                    try:

                        await bot.send_message(
                            chat_id,
                            message
                        )

                    except Exception as error:

                        print(
                            f"Reminder error: {error}"
                        )

                reminder["last_sent"] = today

                changed = True

            if changed:

                save_database(data)

        except Exception as error:

            print(
                f"Reminder loop error: {error}"
            )

        await asyncio.sleep(60)


# ============================================================
# اجرای بات
# ============================================================

async def main():

    create_database()

    print()
    print("====================================")
    print("       🏢 ساختمان فدک")
    print("====================================")
    print("🟢 Bot starting...")
    print("📁 database.json checked")
    print("====================================")
    print()

    reminder_task = asyncio.create_task(
        reminder_loop()
    )

    try:

        await bot.run()

    except KeyboardInterrupt:

        print(
            "\n🔴 Bot stopped."
        )

    finally:

        reminder_task.cancel()

        try:

            await reminder_task

        except asyncio.CancelledError:

            pass


# ============================================================
# Start
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())
