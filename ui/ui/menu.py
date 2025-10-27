#!/usr/bin/env python3
import os
from datetime import datetime, timedelta
import yaml

class InteractiveMenu:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def clear_screen(self):
        os.system('clear')
    
    def run(self):
        self.clear_screen()
        print("=" * 70)
        print("EVENT AGGREGATOR - ВЫБОР ПАРАМЕТРОВ".center(70))
        print("=" * 70)
        print()
        
        print("Выберите подборки (номера через запятую, Enter = все):")
        for i, key in enumerate(self.config['collections'].items(), 1):
            print(f"{i}. {key[1]['name']}")
        
        choice = input("> ").strip()
        collections = list(self.config['collections'].keys()) if not choice else choice
        
        print("\nВыберите территории (номера через запятую, Enter = все):")
        for i, key in enumerate(self.config['territories'].items(), 1):
            print(f"{i}. {key[1]['name']}")
        
        choice = input("> ").strip()
        territories = list(self.config['territories'].keys()) if not choice else choice
        
        today = datetime.now().date()
        
        return {
            'collections': collections,
            'territories': territories,
            'start_date': str(today),
            'end_date': str(today + timedelta(days=7))
        }
