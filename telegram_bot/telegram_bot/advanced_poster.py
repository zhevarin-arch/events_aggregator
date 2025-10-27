#!/usr/bin/env python3
"""
Продвинутая публикация событий в Telegram с форматированием
"""

import os
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdvancedTelegramPoster:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.group_id = int(os.getenv('TELEGRAM_GROUP_ID'))
    
    def format_event(self, event):
        """Красивое форматирование события"""
        title = event.get('title', 'Событие без названия')[:100]
        description = event.get('description', '')[:250]
        price = event.get('price', 'Цена не указана')
        
        message = f"🎭 <b>{title}</b>\n"
        message += f"💰 {price}\n"
        
        if description:
            message += f"📝 {description}\n"
        
        return message
    
    async def send_collection(self, events, thread_id, collection_title):
        """Отправить подборку событий в конкретную тему"""
        if not events:
            logger.warning(f"Нет событий для подборки {collection_title}")
            return False
        
        try:
            # Заголовок подборки
            header = f"✨ <b>{collection_title}</b> ✨\n"
            header += f"Найдено {len(events)} событий\n\n"
            
            await self.bot.send_message(
                chat_id=self.group_id,
                text=header,
                message_thread_id=thread_id,  # ← ЭТО ПУБЛИКУЕТ В КОНКРЕТНУЮ ТЕМУ!
                parse_mode='HTML'
            )
            
            # События
            for i, event in enumerate(events[:10], 1):
                message = f"{i}. {self.format_event(event)}"
                
                await self.bot.send_message(
                    chat_id=self.group_id,
                    text=message,
                    message_thread_id=thread_id,  # ← КАЖДОЕ В ТУ ЖЕ ТЕМУ!
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            
            logger.info(f"✓ Опубликовано {len(events[:10])} событий в тему {thread_id}")
            return True
        
        except TelegramError as e:
            logger.error(f"✗ Ошибка Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Неожиданная ошибка: {e}")
            return False
