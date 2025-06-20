import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import telegram
from telegram import Bot
import re

class SimpleCryptoTracker:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        self.bot = Bot(token=self.bot_token)
        
        # Простая база знаний для описаний (можно расширить)
        self.known_influencers = {
            "Anatoly Yakovenko": "Solana Founder",
            "Vitalik Buterin": "Ethereum Founder", 
            "Fred Ehrsam": "Coinbase Co-founder",
            "Joseph Lubin": "ConsenSys Founder",
            "Hayden Adams": "Uniswap Founder",
            "ZachXBT": "On-chain Detective",
            "David Hoffman": "Bankless Co-founder",
            "Adam Back": "Blockstream CEO",
            "Laura Shin": "Crypto Journalist"
        }
        
        self.known_projects = {
            "Polymarket": "Prediction Market",
            "Uniswap": "DEX Protocol",
            "Solana": "Layer 1 Blockchain",
            "Ethereum": "Layer 1 Blockchain"
        }
    
    def scrape_latest_follows(self):
        """Парсинг последних подписок с rootdata.com/xdata"""
        url = "https://rootdata.com/xdata"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            follows = []
            
            # Парсинг данных (нужно будет адаптировать под реальную структуру HTML)
            # Это пример структуры, которую мы видели на сайте
            follow_items = soup.find_all('div', class_='follow-item')  # Примерный селектор
            
            for item in follow_items:
                try:
                    influencer = item.find('span', class_='influencer-name').text.strip()
                    project = item.find('span', class_='project-name').text.strip()
                    
                    follows.append({
                        'influencer': influencer,
                        'project': project,
                        'type': 'follow',
                        'date': datetime.now().strftime('%Y-%m-%d')
                    })
                except:
                    continue
            
            return follows
            
        except Exception as e:
            print(f"Error scraping data: {e}")
            return []
    
    def get_twitter_link(self, name, is_project=False):
        """Генерация Twitter ссылки (можно улучшить через поиск)"""
        # Простая логика для генерации Twitter ссылок
        clean_name = name.replace(' ', '').lower()
        if is_project:
            return f"https://twitter.com/{clean_name}"
        else:
            # Для инфлюенсеров можно использовать известные хэндлы
            known_handles = {
                "Vitalik Buterin": "VitalikButerin",
                "Anatoly Yakovenko": "aeyakovenko", 
                "Fred Ehrsam": "FEhrsam",
                "Joseph Lubin": "ethereumJoseph",
                "Hayden Adams": "haydenzadams",
                "ZachXBT": "zachxbt"
            }
            handle = known_handles.get(name, clean_name)
            return f"https://twitter.com/{handle}"
    
    def format_message(self, follows_data):
        """Форматирование сообщения для Telegram"""
        if not follows_data:
            return None
            
        today = datetime.now().strftime('%d.%m.%Y')
        
        message = f"""📅 FollowTracker — {today}
🧠 Daily Data:

📈 New Subscriptions:"""
        
        # Ограничиваем до 10 записей, чтобы не превысить лимит Telegram
        for follow in follows_data[:10]:
            influencer = follow['influencer']
            project = follow['project']
            
            # Получаем описания
            influencer_desc = self.known_influencers.get(influencer, "Crypto Influencer")
            project_desc = self.known_projects.get(project, "Crypto Project")
            
            # Получаем Twitter ссылки
            influencer_twitter = self.get_twitter_link(influencer, False)
            project_twitter = self.get_twitter_link(project, True)
            
            # Форматируем строку
            message += f"\n+ [{influencer}]({influencer_twitter}) ({influencer_desc}) → [{project}]({project_twitter}) - {project_desc}"
        
        # Статистика
        message += f"\n\n📊 Daily Stats:"
        message += f"\n- Total new subscriptions: {len(follows_data)}"
        
        # Самый активный инфлюенсер
        if follows_data:
            influencer_counts = {}
            for follow in follows_data:
                inf = follow['influencer']
                influencer_counts[inf] = influencer_counts.get(inf, 0) + 1
            
            most_active = max(influencer_counts, key=influencer_counts.get)
            count = influencer_counts[most_active]
            message += f"\n- Most active influencer: {most_active} ({count} subscriptions)"
        
        return message
    
    def send_to_telegram(self, message):
        """Отправка в Telegram канал"""
        try:
            self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            print("✅ Message sent successfully!")
            return True
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def run(self):
        """Основной метод"""
        print("🚀 Starting Crypto Follow Tracker...")
        
        # Парсим данные
        follows = self.scrape_latest_follows()
        
        if follows:
            print(f"📊 Found {len(follows)} new follows")
            
            # Форматируем сообщение
            message = self.format_message(follows)
            
            if message:
                # Отправляем в Telegram
                success = self.send_to_telegram(message)
                if success:
                    print("🎉 Daily report sent!")
                else:
                    print("❌ Failed to send report")
            else:
                print("⚠️ No message to send")
        else:
            print("📭 No new follows found")

if __name__ == "__main__":
    tracker = SimpleCryptoTracker()
    tracker.run()
