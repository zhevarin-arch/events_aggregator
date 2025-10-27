#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
import asyncio

load_dotenv()

print("=" * 70)
print("ТЕСТИРОВАНИЕ TELEGRAM ПОДКЛЮЧЕНИЯ")
print("=" * 70)

token = os.getenv('TELEGRAM_BOT_TOKEN')
group_id_str = os.getenv('TELEGRAM_GROUP_ID')

print(f"\n📝 Токен: {token[:20]}..." if token else "❌ Токен не найден!")
print(f"📝 Group ID: {group_id_str}")

if not token or not group_id_str:
    print("\n❌ ОШИБКА: .env не заполнен правильно!")
    sys.exit(1)

try:
    group_id = int(group_id_str)
except ValueError:
    print(f"\n❌ ОШИБКА: Group ID должен быть числом, получено: {group_id_str}")
    sys.exit(1)

async def test_telegram():
    """Асинхронная функция для отправки сообщения"""
    try:
        print("\n🔗 Подключение к Telegram API...")
        bot = Bot(token=token)
        
        print("✅ Бот инициализирован")
        
        print(f"\n📨 Отправка сообщения в группу {group_id}...")
        message = await bot.send_message(
            chat_id=group_id,
            text="🎉 Тест! Бот работает!"
        )
        
        print(f"✅ Сообщение отправлено!")
        print(f"   ID сообщения: {message.message_id}")
        print(f"   Текст: {message.text}")
        
    except TelegramError as e:
        print(f"\n❌ Ошибка Telegram: {e}")
        print(f"   Детали: {str(e)}")
        
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()

# Запустить асинхронную функцию
asyncio.run(test_telegram())
