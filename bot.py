from rubpy import BotClient
from rubpy.bot import filters
from rubpy.bot.models import (
    Update,
    Keypad,
    KeypadRow,
    Button,
)
from rubpy.bot.enums import ButtonTypeEnum

bot = BotClient(CCGHHA0UNJQBZMYRHLMIABYBYRPAMRWCYDTOXTFTNEALCJKSGSXXLIWOXJOIPMSU
="CCGHHA0UNJQBZMYRHLMIABYBYRPAMRWCYDTOXTFTNEALCJKSGSXXLIWOXJOIPMSU")


def main_keypad():
    return Keypad(
        rows=[
            KeypadRow(
                buttons=[
                    Button(
                        id="getUpdates",
                        type=ButtonTypeEnum.SIMPLE,
                        button_text="📥 دریافت آخرین آپدیت‌ها",
                    ),
                ]
            ),
            KeypadRow(
                buttons=[
                    Button(
                        id="forwardMessage",
                        type=ButtonTypeEnum.SIMPLE,
                        button_text="↪️ فوروارد کردن پیام",
                    ),
                ]
            ),
            KeypadRow(
                buttons=[
                    Button(
                        id="editMessageText",
                        type=ButtonTypeEnum.SIMPLE,
                        button_text="✏️ ویرایش متن پیام",
                    ),
                    Button(
                        id="editMessageKeypad",
                        type=ButtonTypeEnum.SIMPLE,
                        button_text="🔘 ویرایش کی‌پد",
                    ),
                ]
            ),
        ],
        resize_keyboard=True,
        on_time_keyboard=False,
    )


@bot.on_update(filters.commands("start"))
async def handle_start(bot, update: Update):
    await update.reply(
        "📚 مستندات Rubika Bot API\n\n"
        "متد موردنظر خود را انتخاب کنید:",
        inline_keypad=main_keypad(),
    )


@bot.on_update()
async def handle_buttons(bot, update: Update):
    # نام فیلد callback ممکن است بسته به نسخه rubpy متفاوت باشد.
    # اگر در نسخه شما update وجود داشته باشد، ID دکمه را از آن استخراج کن.
    
    button_id = getattr(update, "button_id", None)

    if button_id == "getUpdates":
        text = """📥 دریافت آخرین آپدیت‌ها

متد: getUpdates

این متد تمامی پیام‌ها، ویرایش‌ها و رویدادهای جدید
مربوط به چت‌ها را از سرور دریافت می‌کند.

ورودی:

• offset_id : string
  شناسه‌ای برای دریافت ادامه‌ی لیست.

• limit : int
  تعداد رکوردهای هر درخواست.

خروجی:

• updates : list[Update]
  آرایه‌ای از آپدیت‌ها.

• next_offset_id : string
  شناسه درخواست بعدی.

نمونه Python:

import requests

data = {
    "limit": limit,
}

url = f"https://botapi.rubika.ir/v3/{CCGHHA0UNJQBZMYRHLMIABYBYRPAMRWCYDTOXTFTNEALCJKSGSXXLIWOXJOIPMSU}/getUpdates"

response = requests.post(
    url,
    json=data
)

print(response.text)
"""

        await update.reply(
            text,
            inline_keypad=main_keypad(),
        )

    elif button_id == "forwardMessage":
        text = """↪️ فوروارد کردن پیام

متد: forwardMessage

این متد پیام موجود در یک چت را به چت دیگری
منتقل می‌کند.

ورودی:

• from_chat_id : string
• message_id : string
• to_chat_id : string
• disable_notification : bool

خروجی:

• new_message_id : string

نمونه Python:

import requests

data = {
    "from_chat_id": chat_id,
    "message_id": message_id,
    "to_chat_id": to_chat_id
}

url = f"https://botapi.rubika.ir/v3/{CCGHHA0UNJQBZMYRHLMIABYBYRPAMRWCYDTOXTFTNEALCJKSGSXXLIWOXJOIPMSU}/forwardMessage"

response = requests.post(
    url,
    json=data
)

print(response.text)
"""

        await update.reply(
            text,
            inline_keypad=main_keypad(),
        )


bot.run()
