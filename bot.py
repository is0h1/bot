import asyncio
import math
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8619139176:AAEqjhRb_ey0Xm9FDrwYlThS5_OQSZcjoU4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Тимчасове сховище для історії покупок (у реальних ботах це База Даних)
user_history = {}


class OrderStars(StatesGroup):
    waiting_for_amount = State()
    confirming_payment = State()


def calculate_price(amount: int):
    rate = 0.84
    return math.ceil(amount * rate)


# --- Клавіатури ---

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⭐ Придбати Stars", callback_data="catalog"))
    builder.row(types.InlineKeyboardButton(text="💎 Власна кількість (від 120)", callback_data="custom_amount"))
    builder.row(types.InlineKeyboardButton(text="👤 Мій кабінет", callback_data="cabinet"))
    builder.row(types.InlineKeyboardButton(text="🆘 Тех. Підтримка", callback_data="support"))
    return builder.as_markup()


def payment_methods():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💳 Monobank", callback_data="confirm_pay"))
    builder.row(types.InlineKeyboardButton(text="🏦 Приват24", callback_data="confirm_pay"))
    builder.row(types.InlineKeyboardButton(text="🍎 Apple / Google Pay", callback_data="confirm_pay"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Скасувати", callback_data="back_home"))
    return builder.as_markup()


# --- Хендлери ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Ініціалізуємо порожню історію для нового користувача
    if message.from_user.id not in user_history:
        user_history[message.from_user.id] = []

    await message.answer(
        "⚡ **StarStore Premium UA**\n\n"
        "Оберіть пакет або введіть кількість зірок для поповнення.",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "cabinet")
async def show_cabinet(callback: types.CallbackQuery):
    u_id = callback.from_user.id
    history_list = user_history.get(u_id, [])

    if not history_list:
        history_text = "💨 У вас поки немає покупок."
    else:
        # Беремо останні 5 покупок
        history_text = "📊 **Останні замовлення:**\n"
        for item in reversed(history_list[-5:]):
            history_text += f"📅 {item['date']} — {item['stars']} ⭐ — **{item['price']} грн** (✅)\n"

    cabinet_text = (
        f"👤 **Особистий кабінет**\n"
        f"ID: `{u_id}`\n"
        f"Статус: VIP\n\n"
        f"{history_text}"
    )

    await callback.message.edit_text(cabinet_text, reply_markup=InlineKeyboardBuilder().row(
        types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")
    ).as_markup())


@dp.callback_query(F.data == "custom_amount")
async def ask_amount(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderStars.waiting_for_amount)
    await callback.message.edit_text("📝 Введіть кількість (від 120 ⭐):",
                                     reply_markup=InlineKeyboardBuilder().row(
                                         types.InlineKeyboardButton(text="⬅️ Назад",
                                                                    callback_data="back_home")).as_markup())


@dp.message(OrderStars.waiting_for_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 120:
        await message.answer("❌ Мінімум 120 зірок. Введіть число:")
        return

    amount = int(message.text)
    price = calculate_price(amount)
    await state.update_data(current_stars=amount, current_price=price)

    await message.answer(f"✅ Замовлення: {amount} ⭐\nСума: **{price} UAH**\nОберіть спосіб оплати:",
                         reply_markup=payment_methods())


@dp.callback_query(F.data.startswith("select_"))
async def select_package(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    amount, price = int(data[1]), int(data[2])
    await state.update_data(current_stars=amount, current_price=price)

    await callback.message.edit_text(f"💎 Пакет: {amount} ⭐\nСума: **{price} UAH**\nОберіть банк:",
                                     reply_markup=payment_methods())


@dp.callback_query(F.data == "confirm_pay")
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stars = data.get("current_stars", 0)
    price = data.get("current_price", 0)
    u_id = callback.from_user.id

    await callback.message.edit_text(
        "⏳ Перевірка транзакції банківською системою...\n\n🛑 *Демо-режим: кошти не списуються.*")
    await asyncio.sleep(2)

    # Додаємо в історію
    new_purchase = {
        "date": datetime.now().strftime("%d.%m.%Y"),
        "stars": stars,
        "price": price
    }

    if u_id not in user_history:
        user_history[u_id] = []
    user_history[u_id].append(new_purchase)

    await callback.message.edit_text(f"✅ Успішно! {stars} ⭐ додано до черги нарахування.", reply_markup=main_menu())
    await state.clear()


@dp.callback_query(F.data == "back_home")
async def back_home_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 Головне меню", reply_markup=main_menu())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
