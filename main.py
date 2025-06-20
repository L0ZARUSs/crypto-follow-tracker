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
        # ✅ ТОКЕНЫ БЕРУТСЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (СЕКРЕТОВ)
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.environ.get('TELEGRAM_CHANNEL_ID', '@cryptohobbys')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables!")
        
        self.bot = Bot(token=self.bot_token)
        self.base_url = "https://www.rootdata.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
    
    def scrape_xdata_pages(self):
        """Скрапинг страниц X Data для получения свежих данных"""
        all_subscriptions = []
        all_unsubscriptions = []
        
        for page in range(1, 4):
            try:
                print(f"🔍 Scraping page {page}...")
                url = f"{self.base_url}/xdata?page={page}" if page > 1 else f"{self.base_url}/xdata"
                
                response = self.session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                subscriptions, unsubscriptions = self.extract_page_data(soup)
                all_subscriptions.extend(subscriptions)
                all_unsubscriptions.extend(unsubscriptions)
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"⚠️ Error scraping page {page}: {e}")
                continue
        
        return all_subscriptions, all_unsubscriptions
    
    def extract_page_data(self, soup):
        """Извлечение данных подписок и отписок"""
        subscriptions = []
        unsubscriptions = []
        
        try:
            # Поиск элементов с действиями
            followed_elements = soup.find_all(text=re.compile(r'Followed', re.I))
            unfollowed_elements = soup.find_all(text=re.compile(r'Unfollowed', re.I))
            
            # Обработка подписок
            for element in followed_elements:
                try:
                    container = element.parent.parent
                    links = container.find_all('a')
                    
                    if len(links) >= 2:
                        influencer_name = links[0].get_text(strip=True)
                        project_name = links[1].get_text(strip=True)
                        project_url = links[1].get('href')
                        
                        if project_url and not project_url.startswith('http'):
                            project_url = urljoin(self.base_url, project_url)
                        
                        subscriptions.append({
                            'influencer_name': influencer_name,
                            'project_name': project_name,
                            'project_url': project_url
                        })
                        
                except Exception:
                    continue
            
            # Обработка отписок
            for element in unfollowed_elements:
                try:
                    container = element.parent.parent
                    links = container.find_all('a')
                    
                    if len(links) >= 2:
                        influencer_name = links[0].get_text(strip=True)
                        
                        for link in links[1:]:
                            project_name = link.get_text(strip=True)
                            project_url = link.get('href')
                            
                            if project_url and not project_url.startswith('http'):
                                project_url = urljoin(self.base_url, project_url)
                            
                            unsubscriptions.append({
                                'influencer_name': influencer_name,
                                'project_name': project_name,
                                'project_url': project_url
                            })
                            
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
        
        return subscriptions, unsubscriptions
    
    def get_project_twitter(self, project_url):
        """Получение Twitter ссылки проекта"""
        if not project_url:
            return None
            
        try:
            time.sleep(random.uniform(1, 2))
            
            response = self.session.get(project_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'twitter.com' in href or 'x.com' in href:
                    if 'twitter.com' in href:
                        return href.split('?')[0]
                    elif 'x.com' in href:
                        return href.replace('x.com', 'twitter.com').split('?')[0]
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error getting Twitter: {e}")
            return None
    
    def get_project_description(self, project_url):
        """Получение описания проекта"""
        if not project_url:
            return "Crypto project"
            
        try:
            response = self.session.get(project_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                desc = meta_desc.get('content', '')
                if desc and len(desc) > 10:
                    return desc[:80] + '...' if len(desc) > 80 else desc
            
            return "Crypto project"
            
        except Exception:
            return "Crypto project"
    
    def enrich_project_data(self, entries, max_entries=5):
        """Обогащение данных проектов"""
        enriched_entries = []
        
        for i, entry in enumerate(entries[:max_entries]):
            print(f"🔍 Getting details for {entry['project_name']} ({i+1}/{min(len(entries), max_entries)})...")
            
            twitter_link = self.get_project_twitter(entry['project_url'])
            description = self.get_project_description(entry['project_url'])
            
            enriched_entry = {
                **entry,
                'twitter_link': twitter_link,
                'description': description
            }
            
            enriched_entries.append(enriched_entry)
            time.sleep(random.uniform(0.5, 1.5))
        
        return enriched_entries
    
    def format_message(self, subscriptions, unsubscriptions):
        """Форматирование сообщения"""
        date_str = datetime.now().strftime("%d.%m.%Y")
        
        message = f"📅 FollowTracker — {date_str}\n"
        message += "🧠 Daily Data:\n\n"
        
        # Новые подписки
        message += "📈 New Subscriptions:\n"
        if subscriptions:
            for sub in subscriptions:
                influencer = sub['influencer_name']
                project_name = sub['project_name']
                description = sub.get('description', 'Crypto project')
                twitter_link = sub.get('twitter_link')
                
                if twitter_link:
                    project_text = f"[{project_name}]({twitter_link}) ({description})"
                else:
                    project_text = f"{project_name} ({description})"
                
                message += f"+ {influencer} → {project_text}\n"
        else:
            message += "No new subscriptions detected today\n"
        
        # Отписки
        message += "\n📉 Unsubscriptions:\n"
        if unsubscriptions:
            for unsub in unsubscriptions:
                influencer = unsub['influencer_name']
                project_name = unsub['project_name']
                description = unsub.get('description', 'Crypto project')
                twitter_link = unsub.get('twitter_link')
                
                if twitter_link:
                    project_text = f"[{project_name}]({twitter_link}) ({description})"
                else:
                    project_text = f"{project_name} ({description})"
                
                message += f"- {influencer} ← {project_text}\n"
        else:
            message += "No unsubscriptions detected today\n"
        
        # Статистика
        message += f"\n📊 Daily Stats:\n"
        message += f"- Total new subscriptions: {len(subscriptions)}\n"
        message += f"- Total unsubscriptions: {len(unsubscriptions)}\n"
        
        if subscriptions:
            influencer_counts = {}
            for sub in subscriptions:
                name = sub['influencer_name']
                influencer_counts[name] = influencer_counts.get(name, 0) + 1
            
            most_active = max(influencer_counts.items(), key=lambda x: x[1])
            if most_active[1] > 1:
                message += f"- Most active influencer: {most_active[0]} ({most_active[1]} subscriptions)"
            else:
                message += f"- Most active influencer: Multiple influencers (1 subscription each)"
        else:
            message += f"- Most active influencer: N/A"
        
        return message
    
    async def send_message(self, message):
        """Отправка сообщения в Telegram"""
        try:
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
        """Основной метод запуска"""
        print("🚀 Starting Crypto Follow Tracker...")
        
        # Скрапинг данных
        subscriptions, unsubscriptions = self.scrape_xdata_pages()
        
        print(f"📊 Found {len(subscriptions)} subscriptions, {len(unsubscriptions
