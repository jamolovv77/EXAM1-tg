from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from service import *
from connection import create_table
import asyncio
import os


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# 🎟️ Менюи асосӣ
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎟️ Мероприятия"),
            KeyboardButton(text="📋 Мои записи")
        ]
    ],
    resize_keyboard=True
)


# 🚀 Оғози бот
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await create_table()

    await message.answer(
        "👋 Салом! Ман боти сабти ном ба чорабиниҳо ҳастам! 🎟️\n"
        "👇 Аз тугмаҳои поён истифода бар!",
        reply_markup=main_menu
    )


# ➕ Илова кардани чорабинӣ
@dp.message(Command("add_event"))
async def cmd_add_event(message: Message, command: CommandObject):
    if command.args is None:
        await message.answer(
            "📝 Намуна:\n/add_event Футбол | 10 | 2026-12-20"
        )
        return

    parts = command.args.split("|")

    if len(parts) != 3:
        await message.answer(
            "❌ Маълумотро бо аломати | ҷудо кунед."
        )
        return

    try:
        title = parts[0].strip()
        capacity = int(parts[1].strip())
        event_date = parts[2].strip()

        if capacity <= 0:
            await message.answer(
                "⚠️ Шумораи ҷойҳо бояд аз 0 зиёд бошад."
            )
            return

        await add_event_db(title, capacity, event_date)

        await message.answer(
            f"✅ Чорабинии «{title}» илова шуд! 🎉"
        )

    except ValueError:
        await message.answer(
            "❌ Шумораи ҷойҳо ё сана нодуруст аст."
        )
    except Exception as error:
        await message.answer(f"⚠️ Хато: {error}")


# 📋 Нишон додани чорабиниҳо
@dp.message(Command("events"))
@dp.message(F.text == "🎟️ Мероприятия")
async def cmd_events(message: Message):
    events = await get_all_events_db()

    if len(events) == 0:
        await message.answer(
            "📭 Ҳоло ягон чорабинӣ нест."
        )
        return

    text = "🎟️ РӮЙХАТИ ЧОРАБИНИҲО:\n\n"

    for event in events:
        text += (
            f"🆔 ID: {event['id']}\n"
            f"📌 Ном: {event['title']}\n"
            f"👥 Ҷойҳо: {event['capacity']}\n"
            f"📅 Сана: {event['event_date']}\n"
            "━━━━━━━━━━━━━━\n"
        )

    text += "\n👇 Барои сабти ном нависед:\n/register ID"

    await message.answer(text)


# 📝 Сабти ном ба чорабинӣ
@dp.message(Command("register"))
async def cmd_register(message: Message, command: CommandObject):
    if command.args is None or not command.args.isdigit():
        await message.answer(
            "⚠️ Намуна: /register 1"
        )
        return

    event_id = int(command.args)
    user_id = str(message.from_user.id)

    status = await register_user_db(user_id, event_id)

    if status == "not_found":
        await message.answer(
            "❌ Чорабинӣ ёфт нашуд."
        )

    elif status == "already_registered":
        await message.answer(
            "⚠️ Шумо аллакай сабти ном шудаед!"
        )

    elif status == "confirmed":
        await message.answer(
            "🎉 Сабти номи шумо тасдиқ шуд! ✅"
        )

    elif status == "waitlist":
        await message.answer(
            "⏳ Ҷойҳо тамом шуданд. Шумо ба рӯйхати интизорӣ дохил шудед."
        )

    else:
        await message.answer(
            "❌ Ҳангоми сабти ном хато шуд."
        )


# ❌ Бекор кардани сабти ном
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, command: CommandObject):
    if command.args is None or not command.args.isdigit():
        await message.answer(
            "⚠️ Намуна: /cancel 1"
        )
        return

    event_id = int(command.args)
    user_id = str(message.from_user.id)

    old_status, promoted_user_id = await cancel_registration_db(
        user_id, event_id
    )

    if old_status is None:
        await message.answer(
            "📭 Шумо дар ин чорабинӣ сабти ном надоред."
        )
        return

    await message.answer(
        "❌ Сабти номи шумо бекор карда шуд."
    )

    if promoted_user_id is not None:
        try:
            await bot.send_message(
                int(promoted_user_id),
                "🎉 Ҷой холӣ шуд! Сабти номи шумо тасдиқ гардид. ✅"
            )
        except Exception:
            pass


# 📋 Нишон додани сабтҳои корбар
@dp.message(Command("my_events"))
@dp.message(F.text == "📋 Мои записи")
async def cmd_my_events(message: Message):
    user_id = str(message.from_user.id)

    events = await get_user_events_db(user_id)

    if len(events) == 0:
        await message.answer(
            "📭 Шумо ҳоло сабти ном надоред."
        )
        return

    text = "📋 САБТҲОИ ШУМО:\n\n"

    for event in events:
        if event["status"] == "confirmed":
            status = "✅ Тасдиқшуда"
        else:
            status = "⏳ Рӯйхати интизорӣ"

        text += (
            f"🆔 ID: {event['id']}\n"
            f"🎟️ Ном: {event['title']}\n"
            f"📅 Сана: {event['event_date']}\n"
            f"📍 Ҳолат: {status}\n"
            "━━━━━━━━━━━━━━\n"
        )

    await message.answer(text)


# 🤖 Ба кор даровардани бот
async def main():
    print("🚀 Бот ба кор шурӯъ кард...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())