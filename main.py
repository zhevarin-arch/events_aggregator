#!/usr/bin/env python3
"""
Event Aggregator - ПОЛНАЯ ВЕРСИЯ (ИСПРАВЛЕННАЯ)
С AI фильтрацией, множественными источниками, полным форматом
"""

import sys
import os
import requests
from datetime import datetime, timedelta
import yaml
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.multi_source_scraper import MultiSourceEventScraper

# Импортируем AI анализатор
try:
    from ai.event_analyzer import EventAnalyzer
    ai_available = True
except:
    ai_available = False

def main():
    print("\n" + "=" * 70)
    print("EVENT AGGREGATOR - ПОЛНАЯ ВЕРСИЯ С AI".center(70))
    print("=" * 70 + "\n")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    group_id = os.getenv('TELEGRAM_GROUP_ID')
    ai_key = os.getenv('OPENROUTER_API_KEY')
    
    if not token or not group_id:
        print("❌ .env не найден!")
        return
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    print("📦 ПОДБОРКА (Enter=1):")
    for i, key in enumerate(config['collections'].keys(), 1):
        print(f"   {i}. {config['collections'][key]['name']}")
    col_idx = int(input("\n> ").strip() or "1") - 1
    collection = list(config['collections'].values())[col_idx]
    
    print("\n📍 ТЕРРИТОРИЯ (Enter=1):")
    for i, key in enumerate(config['territories'].keys(), 1):
        print(f"   {i}. {config['territories'][key]['name']}")
    terr_idx = int(input("\n> ").strip() or "1") - 1
    terr_key = list(config['territories'].keys())[terr_idx]
    territory = config['territories'][terr_key]
    
    print("\n⏰ ПЕРИОД (Enter=3):")
    print("   1. Сегодня")
    print("   2. Завтра")
    print("   3. На неделю")
    print("   4. На месяц")
    period_choice = int(input("\n> ").strip() or "3")
    
    time_ranges = {1: 'today', 2: 'tomorrow', 3: 'week', 4: 'month'}
    time_range = time_ranges.get(period_choice, 'week')
    
    scraper = MultiSourceEventScraper()
    print(f"\n🔄 Сбор: {territory['name']} ({time_range})...")
    print("   Источники: KudaGo, Яндекс.Афиша, Сайты площадок")
    
    # ИСПРАВЛЕНИЕ 1: Убираем лишний параметр
    events = scraper.scrape_all(territory['name'], time_range)
    
    if not events:
        print("❌ События не найдены")
        return
    
    print(f"✓ Найдено {len(events)} событий")
    
    # AI ФИЛЬТРАЦИЯ
    if ai_available and ai_key:
        print("🤖 AI фильтрация событий...")
        analyzer = EventAnalyzer(ai_key)
        
        filtered = []
        for i, event in enumerate(events):
            analysis = analyzer.analyze_quality(event)
            
            # Пропускаем плохие события
            if analysis.get('has_bad_content'):
                continue
            
            if analysis.get('quality', 0) < 5:
                continue
            
            # Добавляем AI данные в событие
            event['quality'] = analysis.get('quality', 5)
            event['ai_summary'] = analysis.get('summary', '')
            event['is_relevant'] = analysis.get('is_relevant', True)
            
            filtered.append(event)
            print(f"   ✓ {i+1}. {event.get('title', '')[:40]}... [качество: {analysis.get('quality', 5)}/10]")
        
        events = filtered
        print(f"✓ После фильтрации: {len(events)} событий")
    
    max_count = min(collection.get('max_count', 10), len(events))
    events = events[:max_count]
    
    if not events:
        print("❌ После фильтрации событий не осталось")
        return
    
    # ФОРМИРУЕМ СООБЩЕНИЕ
    msg = f"✨ <b>{collection['name']}</b> ✨\n"
    msg += f"📍 {territory['name']}\n"
    msg += f"📊 {len(events)} событий\n"
    msg += "=" * 50 + "\n\n"
    
    for i, e in enumerate(events, 1):
        title = e.get('title', 'Событие')[:70]
        date = e.get('date', 'не указано')
        time = e.get('time', '')
        place = e.get('place', 'не указано')[:50]
        price = e.get('price', 'Бесплатно')
        url = e.get('url', '')
        source = e.get('source', 'Неизвестно')
        quality = e.get('quality', '?')
        
        msg += f"<b>{i}. {title}</b>\n"
        msg += f"⭐ Качество: {quality}/10\n"
        msg += f"📅 {date}"
        if time:
            msg += f" в {time}"
        msg += "\n"
        msg += f"📍 {place}\n"
        msg += f"💰 {price}\n"
        msg += f"📌 Источник: {source}\n"
        
        if url:
            msg += f"🔗 <a href='{url}'>Ссылка</a>"
            # Генерируем Яндекс.Карты ссылку
            yandex_url = f"https://yandex.ru/maps/?text={place.replace(' ', '+')}"
            msg += f" | <a href='{yandex_url}'>На карте</a>\n"
        else:
            msg += "\n"
        
        msg += "\n"
    
    # Добавляем общую Яндекс.Карты ссылку
    locations = [e.get('place', '') for e in events if e.get('place')]
    if locations:
        msg += "=" * 50 + "\n"
        msg += "📍 <b>Все события на карте:</b>\n"
        map_url = "https://yandex.ru/maps/?text=" + "%2C".join([l.replace(' ', '+')[:30] for l in locations[:5]])
        msg += f"<a href='{map_url}'>Открыть в Яндекс.Картах</a>\n"
    
    # ИСПРАВЛЕНИЕ 2: Разбиваем длинные сообщения
    try:
        url_api = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Проверка длины сообщения (лимит Telegram = 4096 символов)
        if len(msg) > 4000:
            print(f"⚠️ Сообщение слишком длинное ({len(msg)} символов)")
            print("📦 Разбиваю на части...")
            
            # Разбиваем на части по 3500 символов
            msg_parts = [msg[i:i+3500] for i in range(0, len(msg), 3500)]
            
            for part_num, part in enumerate(msg_parts, 1):
                data = {
                    "chat_id": int(group_id),
                    "text": part,
                    "message_thread_id": territory['thread_id'],
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False
                }
                response = requests.post(url_api, json=data, timeout=10)
                if response.status_code != 200:
                    print(f"❌ Ошибка части {part_num}: {response.text}")
                    return
            
            print(f"✅ Опубликовано {len(events)} событий в {len(msg_parts)} сообщениях!")
        else:
            # Сообщение короткое - отправляем одним куском
            data = {
                "chat_id": int(group_id),
                "text": msg,
                "message_thread_id": territory['thread_id'],
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            response = requests.post(url_api, json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Опубликовано {len(events)} событий!")
                print(f"📱 Сообщение отправлено в Telegram")
            else:
                print(f"❌ Ошибка Telegram: {response.text}")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()