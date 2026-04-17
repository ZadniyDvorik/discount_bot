import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import BOT_TOKEN
from database import (
    get_new_promotions_since, get_users_for_product,
    get_expiring_promotions, Session, Promotion
)

last_check_time = datetime.now()

async def check_new_promotions(bot: Bot):
    global last_check_time
    
    print(f"✔️ Проверка новых акций с {last_check_time.strftime('%H:%M:%S')}")
    
    new_promotions = get_new_promotions_since(last_check_time)
    
    if not new_promotions:
        print("✔️ Новых акций нет")
        return
    
    print(f"✔️ Найдено новых акций: {len(new_promotions)}")
    
    for promo, shop, product in new_promotions:
        users = get_users_for_product(product.id)
        
        if not users:
            continue
        
        discount = int((1 - promo.new_price / promo.old_price) * 100) if promo.old_price else 0
        
        for user in users:
            try:
                message = (
                    f"НОВАЯ АКЦИЯ\n\n"
                    f"Магазин: {shop.name}\n"
                    f"Товар: {product.name}\n"
                    f"Цена: {promo.old_price:.0f}₽ → {promo.new_price:.0f}₽\n"
                    f"Скидка {discount}%\n\n"
                    f"Акция действует до {promo.end_date.strftime('%d.%m.%Y')}\n\n"
                    f"Успейте купить!"
                )
                await bot.send_message(chat_id=user.telegram_id, text=message)
                print(f"✅ Уведомление отправлено пользователю {user.telegram_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки пользователю {user.telegram_id}: {e}")
    
    last_check_time = datetime.now()

async def check_expiring_promotions(bot: Bot):
    print("✔️ Проверка акций, заканчивающихся завтра")
    
    expiring = get_expiring_promotions()
    
    print(f"✔️ Найдено акций, заканчивающихся завтра: {len(expiring)}")
    
    for promo, shop, product in expiring:
        print(f"✔️ Обработка: {product.name} в {shop.name}")
        
        users = get_users_for_product(product.id)
        print(f"✔️ Пользователей с этим товаром: {len(users)}")
        
        if not users:
            print(f"✔️ Нет пользователей для товара {product.name}")
            continue
        
        discount = int((1 - promo.new_price / promo.old_price) * 100) if promo.old_price else 0
        
        for user in users:
            print(f"✔️ Отправка пользователю {user.telegram_id} ({user.first_name})")
            try:
                message = (
                    f"Акция заканчивается завтра!\n\n"
                    f"Магазин: {shop.name}\n"
                    f"Товар: {product.name}\n"
                    f"Цена: {promo.old_price:.0f}₽ → {promo.new_price:.0f}₽\n"
                    f"Скидка {discount}%\n\n"
                    f"Последний день: {promo.end_date.strftime('%d.%m.%Y')}\n\n"
                    f"Успейте купить!"
                )
                await bot.send_message(chat_id=user.telegram_id, text=message)
                print(f"✅ Отправлено!")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
    
    print("✅ Проверка завершена")

def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(check_new_promotions, 'interval', minutes=1, args=[bot])
    
    scheduler.add_job(check_expiring_promotions, 'cron', hour=10, minute=0, args=[bot])
    
    scheduler.start()
    print("✔️ Планировщик уведомлений запущен")
    
    return scheduler