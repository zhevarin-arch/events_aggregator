
#!/usr/bin/env python3
"""
AI Анализатор событий (OpenRouter - бесплатный Google Gemini)
"""

import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EventAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or ""
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
    
    def analyze_quality(self, event):
        """Анализ качества события (0-10) + фильтрация мата + извлечение данных"""
        
        prompt = f"""Анализируй событие:
Название: {event.get('title', '')}
Описание: {event.get('description', '')}
Дата: {event.get('date', '')}
Место: {event.get('place', '')}
Цена: {event.get('price', '')}

ЗАДАЧИ:
1. Оценка качества: от 0 (мусор) до 10 (отличное)
2. Есть ли мат или незаконный контент? (да/нет)
3. Когда происходит событие? (дата в формате DD.MM.YYYY или "не указано")
4. Где происходит? (адрес или место)
5. Краткое описание (макс 100 символов)

Ответь JSON:
{{
  "quality": 8,
  "has_bad_content": false,
  "event_date": "27.10.2025",
  "event_location": "Москва, ул. Петровка, 17",
  "summary": "Концерт...",
  "is_relevant": true
}}"""
        
        try:
            # Используем бесплатный Gemini через OpenRouter
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            response = requests.post(self.endpoint, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Парсим JSON из ответа
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
            
            # Fallback анализ без AI
            return self._fallback_analysis(event)
        
        except Exception as e:
            logger.error(f"AI анализ ошибка: {e}")
            return self._fallback_analysis(event)
    
    def _fallback_analysis(self, event):
        """Базовый анализ без AI"""
        description = event.get('description', '').lower()
        title = event.get('title', '').lower()
        
        # Проверка мата
        bad_words = ['мат', 'взрослый контент']
        has_bad = any(word in description or word in title for word in bad_words)
        
        # Оценка качества по наличию данных
        quality = 5
        if event.get('place'):
            quality += 2
        if event.get('description'):
            quality += 1
        if event.get('price'):
            quality += 1
        if event.get('url'):
            quality += 1
        
        return {
            "quality": min(quality, 10),
            "has_bad_content": has_bad,
            "event_date": event.get('date', 'не указано'),
            "event_location": event.get('place', 'не указано'),
            "summary": event.get('description', '')[:100],
            "is_relevant": quality >= 5 and not has_bad
        }