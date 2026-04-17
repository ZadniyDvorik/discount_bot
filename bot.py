from aiogram import Bot, Dispatcher, types
import logging
import platform
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from aiohttp_socks import ProxyConnector
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN
import asyncio
from notifier import start_scheduler
from database import (
    get_user, add_user,
    find_shops_by_name, get_all_shops,
    add_user_shop, get_user_shops, delete_user_shop,
    get_user_shops_with_coords,
    get_all_products, find_products_by_name,
    add_user_product, get_user_products, delete_user_product,
    get_promotions_for_user
)

PROXY_URL = "http://127.0.0.1:12334"

session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    
    if not user:
        add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        await message.answer(
            f"Привет, {message.from_user.first_name}! \n"
            "Вы зарегистрированы!\n\n"
            "Что я умею:\n"
            "✅ Находить магазины по названию\n"
            "✅ Добавлять магазины в ваш список\n"
            "✅ Отслеживать любимые товары\n"
            "✅ Присылать уведомления о скидках\n\n"
            "Напишите /help, чтобы увидеть все команды",
        )
    else:
        await message.answer(f"С возвращением, {message.from_user.first_name}!\n\n"
            "Напоминаю, что я умею:\n"
            "✅ Находить магазины по названию\n"
            "✅ Добавлять магазины в ваш список\n"
            "✅ Отслеживать любимые товары\n"
            "✅ Присылать уведомления о скидках\n\n"
            "Напишите /help, чтобы увидеть все команды"
        )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n\n"
        "/start — начать работу\n"
        "/help — показать это сообщение\n\n"
        "Магазины:\n"
        "/find_shop <название> — найти магазин\n"
        "/add_shop <название> — добавить магазин в любимые\n"
        "/my_shops — показать мои магазины\n"
        "/all_shops — все магазины в базе\n"
        "/del_shop <название> — удалить магазин из любимых\n"
        "/map — показать магазины на карте\n\n"
        "Товары:\n"
        "/add_product <название> — добавить товар в любимые\n"
        "/my_products — показать любимые товары\n"
        "/del_product <название> — удалить товар из любимых\n\n"
        "Акции:\n"
        "/promotions — все акции в моих любимых магазинах"
    )

@dp.message(Command("find_shop"))
async def cmd_find_shop(message: types.Message):
    query = message.text.replace("/find_shop", "").strip()
    
    if not query:
        await message.answer("Напишите название магазина. Пример: /find_shop Пятёрочка")
        return
    
    shops = find_shops_by_name(query)
    
    if not shops:
        await message.answer(f"Магазины по запросу '{query}' не найдены")
        return
    
    result = f"Найдено магазинов: {len(shops)}\n\n"
    for shop in shops:
        result += f"{shop.name}\n {shop.address}\n"
        if shop.latitude and shop.longitude:
            result += f"Координаты: {shop.latitude}, {shop.longitude}\n"
        result += "\n"
    
    await message.answer(result)

@dp.message(Command("add_shop"))
async def cmd_add_shop(message: types.Message):
    query = message.text.replace("/add_shop", "").strip()
    
    if not query:
        await message.answer("Пример: /add_shop Пятёрочка")
        return
    
    shops = find_shops_by_name(query)
    
    if not shops:
        await message.answer(f"Магазин '{query}' не найден. Сначала используйте /find_shop")
        return
    
    if len(shops) == 1:
        user = get_user(message.from_user.id)
        if not user:
            add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
            user = get_user(message.from_user.id)
        
        add_user_shop(user.id, shops[0].id)
        await message.answer(f"{shops[0].name} добавлен в ваш список")
    
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for shop in shops:
            button = InlineKeyboardButton(
                text=f"{shop.name} — {shop.address[:30]}...",
                callback_data=f"addshop_{shop.id}"
            )
            keyboard.inline_keyboard.append([button])
        
        await message.answer(
            f"Найдено {len(shops)} магазинов. Выберите нужный:",
            reply_markup=keyboard
        )

from aiogram.types import CallbackQuery

@dp.callback_query(lambda c: c.data and c.data.startswith("addshop_"))
async def process_add_shop_callback(callback_query: CallbackQuery):
    shop_id = int(callback_query.data.split("_")[1])
    
    user = get_user(callback_query.from_user.id)
    if not user:
        add_user(callback_query.from_user.id, callback_query.from_user.username, callback_query.from_user.first_name)
        user = get_user(callback_query.from_user.id)
    
    from database import Session, Shop
    session = Session()
    shop = session.query(Shop).filter_by(id=shop_id).first()
    session.close()
    
    if shop:
        add_user_shop(user.id, shop.id)
        await callback_query.message.edit_text(f"{shop.name} добавлен в ваш список")
    else:
        await callback_query.message.edit_text("Магазин не найден")
    
    await callback_query.answer()

@dp.message(Command("all_shops"))
async def cmd_all_shops(message: types.Message):
    from database import get_all_shops
    shops = get_all_shops()
    
    if not shops:
        await message.answer("База магазинов пуста")
        return
    
    result = "Все магазины в базе:\n\n"
    for shop in shops:
        result += f"- {shop.name} — {shop.address}\n"
    
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("my_shops"))
async def cmd_my_shops(message: types.Message):
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        return
    
    shops = get_user_shops(user.id)
    
    if not shops:
        await message.answer("У вас пока нет добавленных магазинов. Используйте /add_shop <название>")
        return
    
    result = "*Ваши магазины:*\n\n"
    for i, shop in enumerate(shops, 1):
        result += f"{i} - {shop.name}\n{shop.address}\n\n"
    
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("del_shop"))
async def cmd_del_shop(message: types.Message):
    query = message.text.replace("/del_shop", "").strip()
    
    if not query:
        await message.answer("Пример: /del_shop Пятёрочка")
        return
    
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        return
    
    user_shops = get_user_shops(user.id)
    
    found = []
    for shop in user_shops:
        if query.lower() in shop.name.lower() or query.lower() in shop.address.lower():
            found.append(shop)
    
    if not found:
        await message.answer(f"Магазин '{query}' не найден в вашем списке")
        return
    
    if len(found) == 1:
        delete_user_shop(user.id, found[0].id)
        await message.answer(f"{found[0].name} ({found[0].address}) удалён из вашего списка")
    
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for shop in found:
            button = InlineKeyboardButton(
                text=f"{shop.name} — {shop.address}",
                callback_data=f"delshop_{shop.id}"
            )
            keyboard.inline_keyboard.append([button])
        
        await message.answer(
            f"Найдено {len(found)} магазинов. Выберите, какой удалить:",
            reply_markup=keyboard
        )


@dp.callback_query(lambda c: c.data and c.data.startswith("delshop_"))
async def process_del_shop_callback(callback_query: CallbackQuery):
    shop_id = int(callback_query.data.split("_")[1])
    
    user = get_user(callback_query.from_user.id)
    if not user:
        await callback_query.message.edit_text("Вы не зарегистрированы")
        await callback_query.answer()
        return
    
    from database import Session, Shop
    session = Session()
    shop = session.query(Shop).filter_by(id=shop_id).first()
    session.close()
    
    if shop:
        delete_user_shop(user.id, shop.id)
        await callback_query.message.edit_text(f"{shop.name} ({shop.address}) удалён из вашего списка")
    else:
        await callback_query.message.edit_text("Магазин не найден")
    
    await callback_query.answer()

@dp.message(Command("add_product"))
async def cmd_add_product(message: types.Message):
    query = message.text.replace("/add_product", "").strip()
    
    if not query:
        await message.answer("Пример: /add_product Молоко")
        return
    
    products = find_products_by_name(query)
    
    if not products:
        await message.answer(f"Товар '{query}' не найден. Доступные товары: /all_products")
        return
    
    if len(products) > 1:
        result = "Уточните название:\n\n"
        for p in products:
            result += f"- {p.name}\n"
        await message.answer(result, parse_mode="Markdown")
        return
    
    user = get_user(message.from_user.id)
    if not user:
        add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
        user = get_user(message.from_user.id)
    
    add_user_product(user.id, products[0].id)
    await message.answer(f"Товар {products[0].name} добавлен в любимые товары")

@dp.message(Command("my_products"))
async def cmd_my_products(message: types.Message):
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Напишите /start для регистрации")
        return
    
    products = get_user_products(user.id)
    
    if not products:
        await message.answer("У вас пока нет любимых товаров. Используйте /add_product")
        return
    
    result = "*Ваши любимые товары:*\n\n"
    for i, p in enumerate(products, 1):
        result += f"{i}. {p.name}\n"
    
    await message.answer(result, parse_mode="Markdown")

@dp.message(Command("del_product"))
async def cmd_del_product(message: types.Message):
    query = message.text.replace("/del_product", "").strip()
    
    if not query:
        await message.answer("Пример: /del_product Молоко")
        return
    
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Напишите /start для регистрации")
        return
    
    products = get_user_products(user.id)
    found = [p for p in products if query.lower() in p.name.lower()]
    
    if not found:
        await message.answer(f"Товар '{query}' не найден в вашем списке")
        return
    
    delete_user_product(user.id, found[0].id)
    await message.answer(f"Товар {found[0].name} удалён из любимых товаров")

@dp.message(Command("map"))
async def cmd_map(message: types.Message):
    from config import YANDEX_MAPS_API_KEY
    import aiohttp
    from aiogram.types import BufferedInputFile
    
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        return
    
    shops = get_user_shops_with_coords(user.id)
    
    if not shops:
        await message.answer("У вас нет магазинов. Добавьте магазин через /add_shop")
        return
    
    center_lat = shops[0].latitude
    center_lon = shops[0].longitude
    
    pt_params = []
    for shop in shops:
        pt_params.append(f"{shop.longitude},{shop.latitude},pm2bl")
    pt_string = "~".join(pt_params)
    
    map_url = (
        f"https://static-maps.yandex.ru/1.x/"
        f"?ll={center_lon},{center_lat}"
        f"&z=12"
        f"&size=600,400"
        f"&l=map"
        f"&pt={pt_string}"
        f"&apikey={YANDEX_MAPS_API_KEY}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(map_url) as resp:
            if resp.status == 200:
                photo_data = await resp.read()
                photo_file = BufferedInputFile(photo_data, filename="map.png")
                await message.answer_photo(
                    photo=photo_file,
                    caption=f"Ваши магазины на карте (всего {len(shops)})"
                )
            else:
                await message.answer(
                    f"Не удалось загрузить статическую карту (ошибка {resp.status})"
                )

@dp.message(Command("promotions"))
async def cmd_promotions(message: types.Message):
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Вы не зарегистрированы. Напишите /start")
        return
    
    promotions = get_promotions_for_user(user.id)
    
    if not promotions:
        await message.answer("В ваших любимых магазинах пока нет активных акций")
        return

    shops_dict = {}
    for promo, shop, product in promotions:
        if shop.id not in shops_dict:
            shops_dict[shop.id] = {
                "name": shop.name,
                "address": shop.address,
                "promotions": []
            }
        shops_dict[shop.id]["promotions"].append((product, promo))

    result = "*Акции в ваших любимых магазинах:*\n\n"
    
    for shop_id, shop_data in shops_dict.items():
        result += f"Магазин: {shop_data['name']}\n"
        result += f"Адрес: {shop_data['address']}\n"
        result += "Акции:\n"
        
        for product, promo in shop_data["promotions"]:
            discount = int((1 - promo.new_price / promo.old_price) * 100) if promo.old_price else 0
            result += f"- {product.name}: {promo.old_price:.0f} руб -> {promo.new_price:.0f} руб (скидка {discount}%)\n"
            if promo.end_date:
                result += f"До {promo.end_date.strftime('%d.%m.%Y')}\n"
        
        result += "\n"
    
    await message.answer(result, parse_mode="Markdown")

async def main():
    scheduler = start_scheduler(bot)
    print("✔️ Бот DiscountBot запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())