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

# .env dosyasyny ýükle
load_dotenv()

# Logging sazlamalary
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SoftwareBot:
    def __init__(self):
        # Environment variables
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')  # @kanaladi ýa-da -100xxxxxxxxx
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        if not all([self.bot_token, self.channel_id, self.gemini_api_key]):
            raise ValueError("Ähli environment variables-lary sazlaň!")

        # Bot we AI setup
        self.bot = Bot(token=self.bot_token)
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')

        # Türkmenistan timezone
        self.timezone = pytz.timezone('Asia/Ashgabat')

        # Bot Şahsyýeti we Ulgam Prompt
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

        # Wagta görä mazmun görnüşleri (täze başlaýanlar üçin)
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

        # Wagta görä tema saýla
        themes = self.wagta_bagly_temalar.get(time_of_day, ["umumy_programma"])
        selected_theme = random.choice(themes)

        # Dinamiki ulgam prompt
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
            # Dinamiki prompt döret
            prompt = self.create_dynamic_prompt()

            # Mazmun döret
            response = self.model.generate_content(prompt)
            content = response.text.strip()

            # Hashtag-lary akylly goş
            hashtags = self.generate_smart_hashtags(content)

            # Soňky mazmun
            final_content = f"{content}\n\n{hashtags}"

            return final_content

        except Exception as e:
            logger.error(f"Mazmun döretmek säwligi: {e}")
            # Fallback - has akylly
            return self.get_fallback_content()

    def generate_smart_hashtags(self, content):
        """Mazmuny görä akylly hashtag döretmek"""
        hashtags = ["#ProgrammaYazmak", "#Kod", "#Öwrenmek"]

        # Mazmuny geçen tehnologiýalara görä hashtag goş
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

        # Wagt esasly hashtag
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
        """Ýalňyşlyk ýagdaýynda ulanyljakly akylly fallback"""
        current_time = datetime.now(self.timezone)

        fallback_messages = [
            f"💡 Şu günler {current_time.strftime('%d %B')} senesinde programma ýazmakda näme öwrendiň?\n\nHer gün kiçi ädim — uly üstünlikleriň açary! Kod ýazmagyň iň owadan taraplary, elmydama täze zatlary öwrenmekdir 🚀",

            f"🤔 Häzir haýsy tehnologiýa bilen işleýärsiň?\n\nMen şu günler kod gözden geçirýän wagtym şeýle pikir etdim: Iň gowy kod diňe işleýän kod däl, beýlekileriň hem aňsat düşünip bilýän kody! 📝",

            f"⚡ Şu wagt {current_time.strftime('%H:%M')} — günüň kod ýazmagyna güýjüň nähili?\n\nKäte iň gowy çözgütler kompýuteri ýapanyňdan soň aklyňa gelýär. Kelle bulaşyk bolsa, gysga gezelenç jadyly bolup biler! 🚶‍♂️"
        ]

        hashtags = "#ProgrammaYazmak #Kod #Howeslendiris #Owrenmek"

        # Telegram'da sorun çıkarmaması için özel karakterleri koruyalım
        safe_base = random.choice(fallback_messages).replace("*", "").replace("_", "").replace("[", "").replace("]", "")

        return f"{safe_base}\n\n{hashtags}"


    async def send_message_to_channel(self, message):
        """Kanala habar ibermek"""
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("Habar üstünlik bilen iberildi!")
            return True
        except TelegramError as e:
            logger.error(f"Telegram ýalňyşlygy: {e}")
            return False
        except Exception as e:
            logger.error(f"Habar ibermek ýalňyşlygy: {e}")
            return False

    async def send_scheduled_content(self):
        """Wagtlaýyn mazmun ibermek - has akylly"""
        logger.info("Akylly mazmun döredilýär...")

        current_time = datetime.now(self.timezone)
        time_of_day = self.get_time_of_day()

        # Wagt esasly başlyk emojilary
        time_emojis = {
            "morning": "🌅",
            "noon": "☀️",
            "afternoon": "🌤️",
            "evening": "🌙"
        }

        # Mazmun döret
        content = await self.generate_content()

        # Wagt maglumatyny goş (az görünýän)
        time_str = current_time.strftime("%H:%M")
        emoji = time_emojis.get(time_of_day, "💻")

        # Soňky habar - has tebigy
        final_message = f"{emoji} {content}"

        success = await self.send_message_to_channel(final_message)
        if success:
            logger.info(f"Akylly mazmun iberildi! [{time_str}]")
        else:
            logger.error("Habar iberilmedi!")

    async def test_message(self):
        """Test habary - tötänleýin mazmun döredýär"""
        print("🤖 Test üçin tötänleýin mazmun döredilýär...")

        # Tötänleýin mazmun döret
        random_content = await self.generate_content()

        # Test sözbaşy goş
        test_content = f"""🧪 **TEST HABARY** - Bot Işleýär! 🎉

{random_content}

---
📅 **Gündelik Programma:**
• 09:00 - Irden maslahat
• 12:00 - Günortan mazmuny
• 16:00 - Ikindi paýlaşymy
• 21:00 - Agşam jemlemesi

#TestBot #ProgrammaBot #Kod"""

        success = await self.send_message_to_channel(test_content)
        if success:
            print("✅ Test habary üstünlik bilen iberildi!")
        else:
            print("❌ Test habary iberilmedi!")

    def schedule_messages(self):
        """Habar wagty bellemek"""
        # Türkmenistan wagty bilen wagtlamak
        schedule.every().day.at("09:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))
        schedule.every().day.at("12:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))
        schedule.every().day.at("16:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))
        schedule.every().day.at("21:00").do(lambda: asyncio.create_task(self.send_scheduled_content()))

        logger.info("Habar wagty bellendi!")
        logger.info("Sagatlar: 09:00, 12:00, 16:00, 21:00 (Türkmenistan)")

    async def run(self):
        """Bot işletmek"""
        print("🤖 Programma Bot başlaýar...")

        # Ilkinji test habary
        await self.test_message()

        # Wagtlamalary sazla
        self.schedule_messages()

        print("⏰ Bot wagtlaşdyrylan habarlar üçin garaşýar...")
        print("📍 Sagatlar: 09:00, 12:00, 16:00, 21:00 (Türkmenistan)")
        print("🛑 Durdurmak üçin Ctrl+C")

        # Esasy aýlaw
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Her minut barla

# El bilen synag funksiýalary
async def send_test_now():
    """Derrew test habary iber"""
    bot = SoftwareBot()
    await bot.test_message()

async def send_random_content():
    """Diňe tötänleýin mazmun iber (test sözbaşy bolmazdan)"""
    bot = SoftwareBot()
    await bot.send_scheduled_content()

async def send_custom_message(message):
    """Özboluşly habar iber"""
    bot = SoftwareBot()
    await bot.send_message_to_channel(message)

if __name__ == "__main__":
    try:
        bot = SoftwareBot()

        # Buýruk setiri argumentleri
        import sys
        if len(sys.argv) > 1:
            if sys.argv[1] == "test":
                # Test habary iber (tötänleýin mazmunly)
                asyncio.run(send_test_now())
            elif sys.argv[1] == "random":
                # Diňe tötänleýin mazmun iber
                asyncio.run(send_random_content())
            elif sys.argv[1] == "message" and len(sys.argv) > 2:
                # Özboluşly habar iber
                custom_msg = " ".join(sys.argv[2:])
                asyncio.run(send_custom_message(custom_msg))
            else:
                print("Ulanyş:")
                print("python bot.py          - Adaty işletmek")
                print("python bot.py test     - Test habary iber (tötänleýin mazmunly)")
                print("python bot.py random   - Diňe tötänleýin mazmun iber")
                print("python bot.py message 'Habar mazmuny' - Özboluşly habar iber")
        else:
            # Adaty işletmek
            asyncio.run(bot.run())

    except KeyboardInterrupt:
        print("\n🛑 Bot durdy!")
    except Exception as e:
        logger.error(f"Umumy ýalňyşlyk: {e}")
        print(f"❌ Ýalňyşlyk: {e}")
