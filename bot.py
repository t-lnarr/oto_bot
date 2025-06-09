import asyncio
import logging
import os
import random
from datetime import datetime, time
import pytz
import google.generativeai as genai
from telegram import Bot
from telegram.error import TelegramError
import schedule
import time as time_module
from dotenv import load_dotenv
import threading
from flask import Flask, jsonify
import signal
import sys

# .env dosyasını yükle (Railway ortam değişkenlerini de destekler)
load_dotenv()

# Flask app (Railway health check için)
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "running",
        "service": "telegram-bot",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SoftwareBot:
    def __init__(self):
        # Environment variables (Railway otomatik olarak sağlar)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Railway port (varsayılan 3000)
        self.port = int(os.getenv('PORT', 3000))

        if not all([self.bot_token, self.channel_id, self.gemini_api_key]):
            raise ValueError("Tüm environment variables'ları ayarlayın!")

        # Bot ve AI kurulumu
        self.bot = Bot(token=self.bot_token)
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')

        # Türkmenistan timezone
        self.timezone = pytz.timezone('Asia/Ashgabat')
        
        # Bot durumu
        self.is_running = True

        # Bot Şahsiyeti ve Sistem Prompt
        self.sen_hakynda = """
        Sen tejribeli programmist we tehnologiýa höweskäri bolan bot.

        KIMSIŇ:
        - 5+ ýyllyk programma ýazmak tejribesi bolan developer
        - Web, mobile, database ýaly köp ugurda tejribeli
        - Täze başlaýanlara we orta derejeli programmistlere kömek edýän
        - Çylşyrymly zatlary ýönekeý düşündirip berýän
        - Dostlukly, ýakyn ýöne professional gatnaşýan

        MAKSADYŇ:
        - Programma ýazyjylary üçin günde 4 gezek peýdaly mazmun paýlaşmak
        - Okyjylara hakykatdanam peýdaly, amaly maglumatlary bermek
        - Täze başlaýanlary we orta derejeli programmistleri höweslendirmek
        - Ylham beriji, höweslendiriji bolmak

        TARZYŇ:
        - Dostlukly we ýakymly dil ulan
        - Emoji ulan ýöne artykmaç däl
        - Gysga, düşnükli we täsirli ýaz
        - Amaly mysallar ber
        - Hekaýa ýaly akyjy söhbetdeş bol
        - Käwagt humor goş

        USSATLYK UGURLARYŇ:
        - Frontend: HTML/CSS, JavaScript, React (başlangyç)
        - Backend: Python, Node.js (ýönekeý)
        - Database: MySQL, PostgreSQL (esasy)
        - Gurallar: VS Code, Git (zerur)
        - Mobil: React Native, Flutter (giriş)
        - Hünärmänlik: Kod häsiýeti, debugging, testing
        - Tejribe: Peýdaly programmalar, kömekçi programmalar
        """

        # Zamana göre içerik türleri
       self.wagta_bagly_temalar = {
            "morning": ["höweslendiriş", "günüň_maslahaty", "irden_iş", "kod_häsiýeti"],
            "noon": ["ýönekeýje_düşündiriş", "şert_tanyşdyryş", "gowy_usullar", "framework_tanyşdyryş"],
            "afternoon": ["mesele_çözmek", "debugging", "kod_düzetmek", "tejribe_paýlaşmak"],
            "evening": ["karýera", "öwrenmek_çeşmeleri", "şahsy_ösüş", "geljekki_maksatlar"]
        }

    def get_time_of_day(self):
        """Günüň haýsy wagty bolandygyny kesgitle"""
        current_hour = datetime.now(self.timezone).hour

        if 6 <= current_hour < 11:
            return "morning"
        elif 11 <= current_hour < 16:
            return "noon"
        elif 16 <= current_hour < 20:
            return "afternoon"
        else:
            return "evening"

    def create_dynamic_prompt(self):
        """Wagta we tötänleýinlige görä dinamiki prompt döret"""
        current_time = datetime.now(self.timezone)
        time_of_day = self.get_time_of_day()
        day_name = current_time.strftime("%A")

        # Zamana göre tema seç
        themes = self.wagta_bagly_temalar.get(time_of_day, ["genel_programlama"])
        selected_theme = random.choice(themes)

        # Dinamik sistem prompt
        system_prompt = f"""
        {self.sen_hakynda}

        HÄZIRKI ÝAGDAÝ:
        - Sene: {current_time.strftime('%d %B %Y')}
        - Gün: {day_name}
        - Sagat: {current_time.strftime('%H:%M')} (Türkmenistan)
        - Günüň Wagty: {time_of_day}
        - Saýlanan Tema: {selected_theme}

        MESELE:
        Bu maglumatlary göz öňünde tutup, häzir kanala programirleme bilen baglanyşykly okajaklary höweslendirjek gowja makalajyk ýaz.

        DÜZGÜNLER:
        1. Doly we özboluşly mazmun döret (şablon ulanma)
        2. Bu wagta we güne laýyk bol
        3. 120-200 söz arasynda ýaz
        4. Amaly, ulanylýan maglumat ber
        5. Höweslendiriji bol
        6. 2-3 emoji ulan (köp däl)
        7. Hashtag goşma (awtomatiki goşaryn)
        8. Kod mysaly bar bolsa ``` bilen ýaz
        9. Hakyky tejribelerinden gürrüň ber
        10. Okyjylar bilen dostlukly söhbetdeş bol
        11. MÖHÜM: Täze başlaýanlar we orta derejeli programmistler üçin düşnükli ýaz
        12. Çylşyrymly adalgalary ulanma, ýönekeý düşündiriş ber
        13. Esasy adalgalary iňlis dilinde aýt
        14. Mysallar getirip görkez.


        GADAGAN ZATLAR:
        - "Salam dostlar" ýaly şablon başlangyjlar
        - Köp emoji
        - Gaýtalanýan sözler
        - Emeli görünýän dil
        - Umumy bilgiler
        - Çylşyrymly tehniki jargon


        Aňsatrak bir kod mysal getirip düşündir ýa-da belli bir tema boýunça zadlar öwret ýa-da bellir bir programirleme dili barada gyzykly faktlar aýdyp ber. Ýa-da programist bolmak üçin hökmany bilmeli zatlar, ulanmaly programmalar barada aýdyp ber. 
        Häzir ajaýyp mazmun döret!
        """

        return system_prompt

    async def generate_content(self):
        """Ýasama akyl bilen doly özboluşly mazmun döretmek"""
        try:
            # Dinamik prompt oluştur
            prompt = self.create_dynamic_prompt()

            # İçerik oluştur
            response = self.model.generate_content(prompt)
            content = response.text.strip()

            # Hashtag'ları akıllı ekle
            hashtags = self.generate_smart_hashtags(content)

            # Son içerik
            final_content = f"{content}\n\n{hashtags}"

            return final_content

        except Exception as e:
            logger.error(f"İçerik oluşturma hatası: {e}")
            # Fallback - daha akıllı
            return self.get_fallback_content()

    def generate_smart_hashtags(self, content):
        """İçeriğe göre akıllı hashtag oluşturma"""
        hashtags = ["#ProgrammaYazmak", "#Kod", "#Öwrenmek"]

        # İçerikte geçen teknolojilere göre hashtag ekle
        tech_keywords = {
            "python": "#Python", "javascript": "#JavaScript", "react": "#React",
            "html": "#HTML", "css": "#CSS", "git": "#Git",
            "api": "#API", "database": "#Database", "mysql": "#MySQL",
            "mobil": "#MobilApp", "web": "#WebDev", "frontend": "#Frontend",
            "backend": "#Backend", "debugging": "#Debugging", "test": "#Testing"
        }

        content_lower = content.lower()
        for keyword, hashtag in tech_keywords.items():
            if keyword in content_lower and hashtag not in hashtags:
                hashtags.append(hashtag)
                if len(hashtags) >= 5:  # Maksimum 5 hashtag
                    break

        # Zaman tabanlı hashtag
        time_of_day = self.get_time_of_day()
        time_hashtags = {
            "morning": "#IrdenkiHöwes",
            "noon": "#GünortaÖwrenmek",
            "afternoon": "#IkindiWagt",
            "evening": "#AgşamDüşünje"
        }

        if time_of_day in time_hashtags:
            hashtags.append(time_hashtags[time_of_day])

        return " ".join(hashtags)

    def get_fallback_content(self):
        """Hata durumunda kullanılacak akıllı fallback"""
        current_time = datetime.now(self.timezone)

        fallback_messages = [
            f"💡 Şu günler {current_time.strftime('%d %B')} senesinde programma ýazmakda näme öwrendiň?\n\nHer gün kiçi ädim — uly üstünlikleriň açary! Kod ýazmagyň iň owadan taraplary, elmydama täze zatlary öwrenmekdir 🚀",

            f"🤔 Häzir haýsy tehnologiýa bilen işleýärsiň?\n\nMen şu günler kod gözden geçirýän wagtym şeýle pikir etdim: Iň gowy kod diňe işleýän kod däl, beýlekileriň hem aňsat düşünip bilýän kody! 📝",

            f"⚡ Şu wagt {current_time.strftime('%H:%M')} — günüň kod ýazmagyna güýjüň nähili?\n\nKäte iň gowy çözgütler kompýuteri ýapanyňdan soň aklyňa gelýär. Kelle bulaşyk bolsa, gysga gezelenç jadyly bolup biler! 🚶‍♂️"
        ]

        hashtags = "#ProgrammaYazmak #Kod #Howeslendiris #Owrenmek"

        safe_base = random.choice(fallback_messages).replace("*", "").replace("_", "").replace("[", "").replace("]", "")

        return f"{safe_base}\n\n{hashtags}"

    async def send_message_to_channel(self, message):
        """Kanala mesaj gönderme"""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("Mesaj başarıyla gönderildi!")
            return True
        except TelegramError as e:
            logger.error(f"Telegram hatası: {e}")
            return False
        except Exception as e:
            logger.error(f"Mesaj gönderme hatası: {e}")
            return False

    async def send_scheduled_content(self):
        """Zamanlanmış içerik gönderme"""
        logger.info("Akıllı içerik oluşturuluyor...")

        current_time = datetime.now(self.timezone)
        time_of_day = self.get_time_of_day()

        # Zaman tabanlı başlık emojileri
        time_emojis = {
            "morning": "🌅",
            "noon": "☀️",
            "afternoon": "🌤️",
            "evening": "🌙"
        }

        # İçerik oluştur
        content = await self.generate_content()

        # Zaman bilgisini ekle
        time_str = current_time.strftime("%H:%M")
        emoji = time_emojis.get(time_of_day, "💻")

        # Son mesaj
        final_message = f"{emoji} {content}"

        success = await self.send_message_to_channel(final_message)
        if success:
            logger.info(f"Akıllı içerik gönderildi! [{time_str}]")
        else:
            logger.error("Mesaj gönderilemedi!")

    async def test_message(self):
        """Test mesajı"""
        print("🤖 Test için rastgele içerik oluşturuluyor...")

        random_content = await self.generate_content()

        test_content = f"""🧪 **TEST MESAJI** - Bot Çalışıyor! 🎉

{random_content}

---
📅 **Günlük Program:**
• 09:00 - Sabah tavsiyesi
• 12:00 - Öğlen içeriği
• 16:00 - İkindi paylaşımı
• 21:00 - Akşam özeti

#TestBot #ProgramBot #Kod"""

        success = await self.send_message_to_channel(test_content)
        if success:
            print("✅ Test mesajı başarıyla gönderildi!")
        else:
            print("❌ Test mesajı gönderilemedi!")

    def schedule_messages(self):
        """Mesaj zamanlaması"""
        # Türkmenistan zamanı ile zamanlama
        schedule.every().day.at("09:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))
        schedule.every().day.at("12:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))
        schedule.every().day.at("16:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))
        schedule.every().day.at("21:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))

        logger.info("Mesaj zamanları ayarlandı!")
        logger.info("Saatler: 09:00, 12:00, 16:00, 21:00 (Türkmenistan)")

    async def run_scheduler(self):
        """Zamanlayıcı döngüsü"""
        while self.is_running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Her dakika kontrol et

    def run_flask_app(self):
        """Flask uygulamasını çalıştır"""
        app.run(host='0.0.0.0', port=self.port, debug=False)

    async def run(self):
        """Bot çalıştırma - Railway için optimize edilmiş"""
        print("🤖 Programlama Bot başlıyor...")
        
        # İlk test mesajı
        await self.test_message()

        # Zamanlamaları ayarla
        self.schedule_messages()

        print("⏰ Bot zamanlanmış mesajlar için bekliyor...")
        print("📍 Saatler: 09:00, 12:00, 16:00, 21:00 (Türkmenistan)")
        print(f"🌐 Flask sunucusu port {self.port}'ta çalışıyor")

        # Flask'ı ayrı thread'de çalıştır
        flask_thread = threading.Thread(target=self.run_flask_app, daemon=True)
        flask_thread.start()

        # Zamanlayıcıyı çalıştır
        await self.run_scheduler()

    def stop(self):
        """Bot'u durdur"""
        self.is_running = False
        logger.info("Bot durduruluyor...")

# Signal handler - Railway için
def signal_handler(signum, frame):
    logger.info(f"Signal {signum} alındı, bot durduruluyor...")
    bot_instance.stop()
    sys.exit(0)

# Manuel test fonksiyonları
async def send_test_now():
    """Hemen test mesajı gönder"""
    bot = SoftwareBot()
    await bot.test_message()

async def send_random_content():
    """Sadece rastgele içerik gönder"""
    bot = SoftwareBot()
    await bot.send_scheduled_content()

async def send_custom_message(message):
    """Özel mesaj gönder"""
    bot = SoftwareBot()
    await bot.send_message_to_channel(message)

# Global bot instance
bot_instance = None

if __name__ == "__main__":
    try:
        bot_instance = SoftwareBot()
        
        # Signal handlers (Railway için)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Komut satırı argümanları
        import sys
        if len(sys.argv) > 1:
            if sys.argv[1] == "test":
                # Test mesajı gönder
                asyncio.run(send_test_now())
            elif sys.argv[1] == "random":
                # Sadece rastgele içerik gönder
                asyncio.run(send_random_content())
            elif sys.argv[1] == "message" and len(sys.argv) > 2:
                # Özel mesaj gönder
                custom_msg = " ".join(sys.argv[2:])
                asyncio.run(send_custom_message(custom_msg))
            else:
                print("Kullanım:")
                print("python bot.py          - Normal çalıştırma")
                print("python bot.py test     - Test mesajı gönder")
                print("python bot.py random   - Rastgele içerik gönder")
                print("python bot.py message 'Mesaj içeriği' - Özel mesaj gönder")
        else:
            # Normal çalıştırma (Railway için)
            asyncio.run(bot_instance.run())

    except KeyboardInterrupt:
        print("\n🛑 Bot durdu!")
    except Exception as e:
        logger.error(f"Genel hata: {e}")
        print(f"❌ Hata: {e}")
