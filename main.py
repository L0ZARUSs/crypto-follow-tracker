import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time
import random
from urllib.parse import urljoin
import re
from telegram import Bot
from telegram.constants import ParseMode

class CryptoFollowTracker:
    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.environ.get('TELEGRAM_CHANNEL_ID', '@cryptohobbys')
        
        print(f"🔍 Bot token found: {'Yes' if self.bot_token else 'No'}")
        print(f"🔍 Channel ID: {self.channel_id}")
        
        if not self.bot_token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN not found!")
        
        self.bot = Bot(token=self.bot_token)
        self.base_url = "https://www.rootdata.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    def scrape_xdata_pages(self):
        """Скрапинг страниц X Data"""
        all_subscriptions = []
        all_unsubscriptions = []
        
        for page in range(1, 3):
            try:
                print(f"🔍 Scraping page {page}...")
                url = f"{self.base_url}/xdata?page={page}" if page > 1 else f"{self.base_url}/xdata"
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                subscriptions, unsubscriptions = self.extract_page_data(soup)
                all_subscriptions.extend(subscriptions)
                all_unsubscriptions.extend(unsubscriptions)
                
                print(f"📊 Page {page}: {len(subscriptions)} subscriptions, {len(unsubscriptions)} unsubscriptions")
                
                if page < 2:
                    time.sleep(3)
                
            except Exception as e:
                print(f"⚠️ Error scraping page {page}: {e}")
                continue
        
        return all_subscriptions, all_unsubscriptions
    
    def extract_page_data(self, soup):
        """Извлечение данных со страницы"""
        subscriptions = []
        unsubscriptions = []
        
        try:
            page_text = soup.get_text()
            lines = page_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if 'Followed' in line and 'Unfollowed' not in line:
                    parts = line.split('Followed')
                    if len(parts) >= 2:
                        influencer = parts[0].strip()
                        project = parts[1].strip()
                        
                        if influencer and project and len(influencer) > 2 and len(project) > 2:
                            subscriptions.append({
                                'influencer_name': influencer,
                                'project_name': project,
                                'project_url': None,
                                'description': 'Crypto project'
                            })
                
                elif 'Unfollowed' in line:
                    parts = line.split('Unfollowed')
                    if len(parts) >= 2:
                        influencer = parts[0].strip()
                        project = parts[1].strip()
                        
                        if influencer and project and len(influencer) > 2 and len(project) > 2:
                            unsubscriptions.append({
                                'influencer_name': influencer,
                                'project_name': project,
                                'project_url': None,
                                'description': 'Crypto project'
                            })
                            
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
        
        return subscriptions[:10], unsubscriptions[:5]
    
    def format_message(self, subscriptions, unsubscriptions):
        """Форматирование сообщения"""
        date_str = datetime.now().strftime("%d.%m.%Y")
        
        message = f"📅 FollowTracker — {date_str}\n"
        message += "🧠 Daily Data:\n\n"
        
        # Новые подписки
        message += "📈 New Subscriptions:\n"
        if subscriptions:
            for sub in subscriptions[:5]:
                influencer = sub['influencer_name']
                project_name = sub['project_name']
                description = sub.get('description', 'Crypto project')
                
                message += f"+ {influencer} → {project_name} ({description})\n"
        else:
            message += "No new subscriptions detected today\n"
        
        # Отписки
        message += "\n📉 Unsubscriptions:\n"
        if unsubscriptions:
            for unsub in unsubscriptions[:3]:
                influencer = unsub['influencer_name']
                project_name = unsub['project_name']
                description = unsub.get('description', 'Crypto project')
                
                message += f"- {influencer} ← {project_name} ({description})\n"
        else:
            message += "No unsubscriptions detected today\n"
        
        # Статистика
        message += f"\n📊 Daily Stats:\n"
        message += f"- Total new subscriptions: {len(subscriptions)}\n"
        message += f"- Total unsubscriptions: {len(unsubscriptions)}\n"
        message += f"- Most active influencer: Multiple influencers (1 subscription each)"
        
        return message
    
    async def send_message(self, message):
        """Отправка сообщения"""
        try:
            print("📤 Sending message to Telegram...")
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
            print("✅ Message sent successfully!")
            return True
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    async def run(self):
        """Основной метод"""
        try:
            print("🚀 Starting Crypto Follow Tracker...")
            
            # Скрапинг данных
            subscriptions, unsubscriptions = self.scrape_xdata_pages()
            
            print(f"📊 Total found: {len(subscriptions)} subscriptions, {len(unsubscriptions)} unsubscriptions")
            
            # Форматирование и отправка
            message = self.format_message(subscriptions, unsubscriptions)
            success = await self.send_message(message)
            
            if success:
                print("✅ Crypto Follow Tracker completed successfully!")
            else:
                print("❌ Failed to send message")
                
        except Exception as e:
            print(f"❌ Critical error: {e}")
            raise

async def main():
    """Главная функция"""
    try:
        tracker = CryptoFollowTracker()
        await tracker.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
