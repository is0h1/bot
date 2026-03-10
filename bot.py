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

# Назва твого магазину
SHOP_NAME = "StarCapital UA"

# Тимчасова база даних
user_history = {}


class OrderStars(StatesGroup):
    waiting_for_amount = State()


def calculate_price(amount: int):
    # Твій прайс: 30=22, 50=39, 100=84. Це приблизно 0.84 грн за шт.
    rate = 0.84
    return math.ceil(amount * rate)


# --- Клавіатури ---

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⭐ Придбати Stars", callback_data="catalog"))
    builder.row(types.InlineKeyboardButton(text="💎 Своя кількість (від 120)", callback_data="custom_amount"))
    builder.row(types.InlineKeyboardButton(text="👤 Мій кабінет", callback_data="cabinet"))
    builder.row(types.InlineKeyboardButton(text="🆘 Підтримка", callback_data="support"))
    return builder.as_markup()


def payment_methods():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💳 Monobank", callback_data="confirm_pay"))
    builder.row(types.InlineKeyboardButton(text="🏦 Приват24", callback_data="confirm_pay"))
    builder.row(types.InlineKeyboardButton(text="🍎 Apple / Google Pay", callback_data="confirm_pay"))
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home"))
    return builder.as_markup()


# --- Хендлери ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id not in user_history:
        user_history[message.from_user.id] = []

    await message.answer(
        f"🌟 Вітаємо у **{SHOP_NAME}**!\n\n"
        "Найшвидше поповнення Telegram Stars в Україні.\n"
        "Оберіть потрібну кількість зірок:",
        reply_markup=main_menu()
    )


# Каталог готових пакетів
@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    # (Кількість зірок, Ціна в грн)
    packages = [(30, 22), (50, 39), (100, 84)]

    for amount, price in packages:
        builder.row(types.InlineKeyboardButton(
            text=f"{amount} ⭐ — {price} грн",
            callback_data=f"buy_pack_{amount}_{price}")  # Виправлено тут
        )

    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home"))
    await callback.message.edit_text("🔥 **Популярні пакети:**", reply_markup=builder.as_markup())


# Власна кількість
@dp.callback_query(F.data == "custom_amount")
async def ask_amount(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderStars.waiting_for_amount)
    await callback.message.edit_text(
        "📝 **Вкажіть кількість зірок:**\n"
        "(Мінімально: 120 ⭐)",
        reply_markup=InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")).as_markup()
    )


@dp.message(OrderStars.waiting_for_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 120:
        await message.answer("⚠️ Помилка! Введіть число не менше 120.")
        return

    amount = int(message.text)
    price = calculate_price(amount)

    # Зберігаємо дані в стан, щоб не загубити при оплаті
    await state.update_data(current_stars=amount, current_price=price)

    await message.answer(
        f"💎 **Ваше замовлення:**\n"
        f"Кількість: {amount} ⭐\n"
        f"Ціна: **{price} UAH**\n\n"
        f"Оберіть спосіб оплати:",
        reply_markup=payment_methods()
    )


# Обробка вибору готового пакету
@dp.callback_query(F.data.startswith("buy_pack_"))
async def select_package(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    amount = int(data[2])
    price = int(data[3])

    await state.update_data(current_stars=amount, current_price=price)

    await callback.message.edit_text(
        f"💎 **Ваше замовлення:**\n"
        f"Пакет: {amount} ⭐\n"
        f"Ціна: **{price} UAH**\n\n"
        f"Оберіть банк для оплати:",
        reply_markup=payment_methods()
    )


# Кнопка Оплатити
@dp.callback_query(F.data == "confirm_pay")
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stars = data.get("current_stars")
    price = data.get("current_price")

    if not stars:  # Якщо дані з якоїсь причини зникли
        await callback.answer("⚠️ Помилка замовлення. Спробуйте ще раз.", show_alert=True)
        return

    await callback.message.edit_text(
        f"📡 З'єднання з банком...\nСума: {price} UAH\n\n🛑 *Це демо-режим. Кошти не знімаються.*")
    await asyncio.sleep(2)

    # Запис в історію
    u_id = callback.from_user.id
    if u_id not in user_history: user_history[u_id] = []

    user_history[u_id].append({
        "date": datetime.now().strftime("%d.%m.%Y"),
        "stars": stars,
        "price": price
    })

    await callback.message.edit_text(
        f"✅ **Оплата успішна!**\n\n"
        f"{stars} ⭐ буде нараховано протягом декількох хвилин.\n"
        f"Дякуємо, що обрали {SHOP_NAME}!",
        reply_markup=main_menu()
    )
    await state.clear()


# Кабінет
@dp.callback_query(F.data == "cabinet")
async def show_cabinet(callback: types.CallbackQuery):
    u_id = callback.from_user.id
    history_list = user_history.get(u_id, [])

    if not history_list:
        history_text = "💨 У вас ще немає замовлень."
    else:
        history_text = "📊 **Останні замовлення:**\n"
        for item in reversed(history_list[-5:]):
            history_text += f"📅 {item['date']} — {item['stars']} ⭐ — {item['price']} грн (✅)\n"

    await callback.message.edit_text(
        f"👤 **Кабінет {callback.from_user.first_name}**\n"
        f"ID: `{u_id}`\n\n"
        f"{history_text}",
        reply_markup=InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")).as_markup()
    )


@dp.callback_query(F.data == "support")
async def support_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛠 **Підтримка**\n\nДля вирішення проблем пишіть: @ZirkaPay_Admin",
        reply_markup=InlineKeyboardBuilder().row(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_home")).as_markup()
    )


@dp.callback_query(F.data == "back_home")
async def back_home_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🏠 Головне меню", reply_markup=main_menu())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
