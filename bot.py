import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Встав сюди свій токен від BotFather
TOKEN = "8619139176:AAEqjhRb_ey0Xm9FDrwYlThS5_OQSZcjoU4"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Головне меню
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✨ Обрати зірку", callback_data="catalog"))
    builder.row(types.InlineKeyboardButton(text="📜 Мої замовлення", callback_data="orders"))
    builder.row(types.InlineKeyboardButton(text="🆘 Підтримка", callback_data="support"))
    return builder.as_markup()


# Старт
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Вітаємо у **StarStore Premium**! 🌌\n\n"
        "Ми — єдиний сервіс у галактиці, де ви можете придбати власну зірку.\n"
        "Оберіть ділянку неба, щоб почати.",
        reply_markup=main_menu()
    )


# Каталог
@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    stars = [
        ("Синій Гігант", "500$"),
        ("Червоний Карлик", "150$"),
        ("Нейтронна зірка", "1200$")
    ]
    for name, price in stars:
        builder.row(types.InlineKeyboardButton(text=f"{name} — {price}", callback_data=f"buy_{name}"))

    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main"))

    await callback.message.edit_text("Оберіть тип небесного тіла:", reply_markup=builder.as_markup())


# Імітація купівлі
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    star_name = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💳 Підтвердити та оплатити", callback_data="fake_pay"))
    builder.row(types.InlineKeyboardButton(text="❌ Скасувати", callback_data="catalog"))

    await callback.message.edit_text(
        f"Ви обрали: **{star_name}**.\n\n"
        "Для демонстраційного релізу активовано режим 'Тестова оплата'.\n"
        "Кошти з вашого рахунку списані не будуть.",
        reply_markup=builder.as_markup()
    )


# Фінал "оплати"
@dp.callback_query(F.data == "fake_pay")
async def finish_deal(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "✅ **Успішно!**\n\n"
        "Ваша транзакція оброблена. Сертифікат на володіння зіркою надіслано на вашу електронну пошту.\n\n"
        "Дякуємо, що обрали StarStore!",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "back_to_main")
async def back_home(callback: types.CallbackQuery):
    await callback.message.edit_text("Головне меню:", reply_markup=main_menu())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())