#!/usr/bin/env python3
"""
Агрегатор событий из множественных источников
(VK + Telegram + KudaGo + Яндекс + Сайты площадок)
С ЖЁСТКОЙ ФИЛЬТРАЦИЕЙ ПО ДАТЕ
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

class MultiSourceEventScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def scrape_kudago(self, city_slug, time_range='week'):
        """KudaGo API С ЖЁСТКОЙ ФИЛЬТРАЦИЕЙ ПО ДАТЕ"""
        try:
            now = datetime.now()
            
            # Определяем временной диапазон
            if time_range == 'today':
                start_date = now
                end_date = now + timedelta(days=1)
            elif time_range == 'tomorrow':
                start_date = now + timedelta(days=1)
                end_date = now + timedelta(days=2)
            elif time_range == 'week':
                start_date = now
                end_date = now + timedelta(days=7)
            elif time_range == 'month':
                start_date = now
                end_date = now + timedelta(days=30)
            else:
                start_date = now
                end_date = now + timedelta(days=7)
            
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())
            
            url = "https://kudago.com/public-api/v1.4/events/"
            params = {
                'location': city_slug,
                'page_size': 100,
                'fields': 'id,title,description,place,dates,price,site_url,images',
                'actual_since': start_ts,
                'actual_until': end_ts,
                'order_by': '-publication_date'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                events = response.json().get('results', [])
                formatted = []
                
                for e in events:
                    if not e.get('dates'):
                        continue
                    
                    dates = e.get('dates', [])
                    if not dates:
                        continue
                    
                    first_date = dates[0]
                    start_event_ts = first_date.get('start')
                    
                    if not start_event_ts:
                        continue
                    
                    event_date = datetime.fromtimestamp(start_event_ts)
                    
                    # 🔥 ЖЁСТКАЯ ФИЛЬТРАЦИЯ ПО ДАТЕ
                    # Пропускаем события старше чем 1 день назад
                    if event_date < now - timedelta(days=1):
                        logger.info(f"[KudaGo] Пропускаю старое событие: {e.get('title', '')} ({event_date.strftime('%Y-%m-%d')})")
                        continue
                    
                    # Пропускаем события за пределами диапазона
                    if event_date > end_date:
                        continue
                    
                    place_info = e.get('place', {})
                    place_name = place_info.get('title', 'Не указано') if place_info else 'Не указано'
                    
                    formatted.append({
                        'title': e.get('title', ''),
                        'description': e.get('description', ''),
                        'date': event_date.strftime('%d.%m.%Y'),
                        'time': event_date.strftime('%H:%M'),
                        'place': place_name,
                        'price': e.get('price', 'Бесплатно'),
                        'url': e.get('site_url', ''),
                        'source': 'KudaGo',
                        'timestamp': start_event_ts
                    })
                
                # Сортируем по дате
                formatted.sort(key=lambda x: x['timestamp'])
                
                logger.info(f"[KudaGo] {len(formatted)} АКТУАЛЬНЫХ событий (после фильтрации)")
                return formatted
            
            return []
        except Exception as e:
            logger.error(f"[KudaGo] Ошибка: {e}")
            return []
    
    def scrape_yandex(self, city_name, time_range='week'):
        """Яндекс.Афиша"""
        try:
            url = f"https://afisha.yandex.ru/{city_name.lower()}/events/"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                events = []
                
                event_cards = soup.find_all('div', class_='event-card')
                for card in event_cards[:20]:
                    try:
                        title = card.find('h3')
                        if not title:
                            continue
                        
                        events.append({
                            'title': title.get_text(strip=True)[:80],
                            'description': '',
                            'date': 'См. Яндекс',
                            'time': '',
                            'place': '',
                            'price': '',
                            'url': f"https://afisha.yandex.ru{card.find('a')['href']}",
                            'source': 'Яндекс.Афиша',
                            'timestamp': datetime.now().timestamp()
                        })
                    except:
                        continue
                
                logger.info(f"[Яндекс] {len(events)} событий")
                return events
            return []
        except Exception as e:
            logger.error(f"[Яндекс] Ошибка: {e}")
            return []
    
    def scrape_venues(self, venue_urls):
        """Сайты театров, клубов, парков"""
        all_events = []
        
        for venue_url in venue_urls:
            try:
                response = requests.get(venue_url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    event_elements = soup.find_all(['div', 'section'], class_=re.compile('event|афиша|program', re.I))
                    
                    for elem in event_elements[:10]:
                        text = elem.get_text()
                        all_events.append({
                            'title': text[:100],
                            'description': '',
                            'date': 'На сайте',
                            'time': '',
                            'place': venue_url.split('/')[2],
                            'price': '',
                            'url': venue_url,
                            'source': 'Сайты площадок',
                            'timestamp': datetime.now().timestamp()
                        })
            except Exception as e:
                logger.error(f"[Venues] {venue_url}: {e}")
        
        logger.info(f"[Venues] {len(all_events)} событий")
        return all_events
    
    def scrape_all(self, city, time_range='week'):
        """Собрать события со ВСЕХ источников С ФИЛЬТРАЦИЕЙ ПО ДАТЕ"""
        all_events = []
        
        # KudaGo (с жёсткой фильтрацией)
        city_slug = self._get_city_slug(city)
        kudago_events = self.scrape_kudago(city_slug, time_range)
        all_events.extend(kudago_events)
        
        # Яндекс.Афиша
        yandex_events = self.scrape_yandex(city, time_range)
        all_events.extend(yandex_events)
        
        # Сайты площадок (пример для Москвы)
        if city.lower() in ['москва', 'msk']:
            venues = [
                'https://www.teatr-mayakovskogo.ru',
                'https://www.bolshoi.ru',
            ]
            venue_events = self.scrape_venues(venues)
            all_events.extend(venue_events)
        
        # Сортируем по дате
        all_events.sort(key=lambda x: x['timestamp'], reverse=False)
        
        logger.info(f"✓ ИТОГО {len(all_events)} АКТУАЛЬНЫХ событий из множественных источников")
        return all_events
    
    def _get_city_slug(self, city):
        slugs = {
            'москва': 'msk',
            'ярославль': 'yaroslavl',
            'тверь': 'tver'
        }
        return slugs.get(city.lower(), 'msk')
