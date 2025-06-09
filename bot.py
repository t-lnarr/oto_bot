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

# .env faýlyny ýükle (Railway gurşaw üýtgeýjilerini hem goldaýar)
load_dotenv()

# Flask app (Railway saglygy barlagy üçin)
app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "işleýär",
        "hyzmat": "telegram-bot",
        "wagt": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "sagdyn"})

# Gündelik ýazgysy sazlamalary
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ProgrammaBot:
    def __init__(self):
        # Gurşaw üýtgeýjileri (Railway awtomatiki üpjün edýär)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.kanal_id = os.getenv('TELEGRAM_CHANNEL_ID')
        self.gemini_api_açar = os.getenv('GEMINI_API_KEY')

        # Railway porty (esasy 3000)
        self.port = int(os.getenv('PORT', 3000))

        if not all([self.bot_token, self.kanal_id, self.gemini_api_açar]):
            raise ValueError("Ähli gurşaw üýtgeýjilerini sazlaň!")

        # Bot we AI gurluşy
        self.bot = Bot(token=self.bot_token)
        genai.configure(api_key=self.gemini_api_açar)
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')

        # Türkmenistan wagt zolagy
        self.wagt_zolagy = pytz.timezone('Asia/Ashgabat')

        # Bot ýagdaýy
        self.işleýär = True

        # Bot Şahsyýeti we Ulgam Tabşyrygy
        self.sen_hakynda = """
        Sen tejribeli programmist we tehnologiýa höweskäri bolan bot.

        KIMSIŇ:
        - 5+ ýyllyk programma ýazmak tejribesi bolan developer
        - Web, mobil, database ýaly köp ugurda tejribeli
        - Täze başlaýanlara we orta derejeli programmistlere kömek edýän
        - Çylşyrymly zatlary ýönekeý düşündirip bilýän
        - Dostlukly, ýakyn ýöne professional gatnaşýan

        MAKSADYŇ:
        - Programma ýazyjylary üçin günde 4 gezek peýdaly mazmun paýlaşmak
        - Okyjylara hakykatdanam peýdaly, amaly maglumatlary bermek
        - Täze başlaýanlary we orta derejeli programmistleri höweslendirmek
        - Ylham beriji, höweslendiriji bolmak

        STILIŇ:
        - Dostlukly we ýakymly dil ulan
        - Emoji ulan ýöne artykmaç däl
        - Gysga, düşnükli we täsirli ýaz
        - Amaly mysallar ber
        - Hekaýa ýaly akyjy söhbetdeş bol
        - Käwagt humor goş

        USSATLYK UGURLARYŇ:
        - Frontend: HTML/CSS, JavaScript, React (başlangyç)
        - Backend: Python, Node.js (ýönekeý)
        - Maglumat bazasy: MySQL, PostgreSQL (esasy)
        - Gurallar: VS Code, Git (zerur)
        - Mobil: React Native, Flutter (giriş)
        - Hünärmänlik: Kod häsiýeti, debugging, testing
        - Tejribe: Peýdaly programmalar, kömekçi programmalar
        """

        # Wagta görä mazmun görnüşleri
        self.wagta_bagly_temalar = {
            "ertir": ["höweslendiriji", "günüň_maslahaty", "irden_iş", "kod_häsiýeti"],
            "günorta": ["ýönekeýje_düşündiriş", "algoritma_tanyşdyryş", "gowy_usullar", "framework_tanyşdyryş"],
            "ikindi": ["mesele_çözmek", "debugging", "kod_düzetmek", "tejribe_paýlaşmak"],
            "agşam": ["karýera", "öwrenmek_üçin_çeşmeler", "şahsy_ösüş", "geljekki_maksatlar"]
        }

    def günüň_wagty(self):
        """Günüň haýsy wagty bolandygyny kesgitle"""
        häzirki_sagat = datetime.now(self.wagt_zolagy).hour

        if 6 <= häzirki_sagat < 11:
            return "ertir"
        elif 11 <= häzirki_sagat < 16:
            return "günorta"
        elif 16 <= häzirki_sagat < 20:
            return "ikindi"
        else:
            return "agşam"

    def dinamiki_tabşyryk_döret(self):
        """Wagta we tötänleýinlige görä dinamiki tabşyryk döret"""
        häzirki_wagt = datetime.now(self.wagt_zolagy)
        günüň_wagty = self.günüň_wagty()
        günüň_ady = häzirki_wagt.strftime("%A")

        # Wagta görä tema saýla
        temalar = self.wagta_bagly_temalar.get(günüň_wagty, ["umumy_programma"])
        saýlanan_tema = random.choice(temalar)

        # Dinamiki ulgam tabşyrygy
        ulgam_tabşyrygy = f"""
        {self.sen_hakynda}

        HÄZIRKI ÝAGDAÝ:
        - Sene: {häzirki_wagt.strftime('%d %B %Y')}
        - Gün: {günüň_ady}
        - Sagat: {häzirki_wagt.strftime('%H:%M')} (Türkmenistan)
        - Günüň Wagty: {günüň_wagty}
        - Saýlanan Tema: {saýlanan_tema}

        MESELE:
        Bu maglumatlary göz öňünde tutup, häzir kanala programmirlemek bilen bagly okyjylary höweslendirjek gowy mazmun ýaz.

        DÜZGÜNLER:
        1. Doly we özboluşly mazmun döret (şablon ulanma)
        2. Bu wagta we güne laýyk bol
        3. 120-200 söz arasynda ýaz
        4. Amaly, ulanylýan maglumat ber
        5. Höweslendiriji bol
        6. 2-3 emoji ulan (köp däl)
        7. Hashtag goşma (awtomatiki goşaryn)
        8. Kod mysaly bar bolsa ``` bilen ýaz
        9. Hakyky tejribelerden gürrüň ber
        10. Okyjylar bilen dostlukly söhbetdeş bol
        11. MÖHÜM: Täze başlaýanlar we orta derejeli programmistler üçin düşnükli ýaz
        12. Çylşyrymly adalgalary ulanma, ýönekeý düşündiriş ber
        13. Esasy adalgalary iňlis dilinde aýt
        14. Mysallar getirip görkez

        GADAGAN ZATLAR:
        - "Salam dostlar" ýaly şablon başlangyjlar
        - Köp emoji
        - Gaýtalanýan sözler
        - Emeli görünýän dil
        - Umumy bilgiler
        - Çylşyrymly tehniki jargon

        Aňsatrak bir kod mysaly getirip düşündir ýa-da belli bir tema boýunça zatlar öwret ýa-da belli bir programmirlemek dili barada gyzykly faktlar aýdyp ber. Ýa-da programmist bolmak üçin hökmany bilmeli zatlar, ulanmaly programmalar barada aýdyp ber.
        Häzir ajaýyp mazmun döret!
        """

        return ulgam_tabşyrygy

    async def mazmun_döret(self):
        """Emeli aň bilen doly özboluşly mazmun döretmek"""
        try:
            # Dinamiki tabşyryk döret
            tabşyryk = self.dinamiki_tabşyryk_döret()

            # Mazmun döret
            jogap = self.model.generate_content(tabşyryk)
            mazmun = jogap.text.strip()

            # Hashtag'lary akylly goş
            hashtag_lar = self.akylly_hashtag_döret(mazmun)

            # Soňky mazmun
            ahyrky_mazmun = f"{mazmun}\n\n{hashtag_lar}"

            return ahyrky_mazmun

        except Exception as e:
            logger.error(f"Mazmun döretmekde ýalňyşlyk: {e}")
            # Ätiýaçlyk - has akylly
            return self.ätiýaçlyk_mazmun_al()

    def akylly_hashtag_döret(self, mazmun):
        """Mazmuna görä akylly hashtag döretmek"""
        hashtag_lar = ["#ProgrammaYazmak", "#Kod", "#Öwrenmek"]

        # Mazmunyň içinde geçýän tehnologiýalara görä hashtag goş
        tehno_açar_sözler = {
            "python": "#Python", "javascript": "#JavaScript", "react": "#React",
            "html": "#HTML", "css": "#CSS", "git": "#Git",
            "api": "#API", "database": "#MaglumatBazasy", "mysql": "#MySQL",
            "mobil": "#MobilApp", "web": "#WebDev", "frontend": "#Frontend",
            "backend": "#Backend", "debugging": "#Debugging", "test": "#Testing"
        }

        mazmun_kiçi = mazmun.lower()
        for açar_söz, hashtag in tehno_açar_sözler.items():
            if açar_söz in mazmun_kiçi and hashtag not in hashtag_lar:
                hashtag_lar.append(hashtag)
                if len(hashtag_lar) >= 5:  # Iň köp 5 hashtag
                    break

        # Wagta esaslanan hashtag
        günüň_wagty = self.günüň_wagty()
        wagt_hashtag_lary = {
            "ertir": "#IrdenkiStart",
            "günorta": "#ObetkiWork",
            "ikindi": "#IkindiTime",
            "agşam": "#AgşamkyIdea"
        }

        if günüň_wagty in wagt_hashtag_lary:
            hashtag_lar.append(wagt_hashtag_lary[günüň_wagty])

        return " ".join(hashtag_lar)

    def ätiýaçlyk_mazmun_al(self):
        """Ýalňyşlyk ýagdaýynda ulanylajak akylly ätiýaçlyk"""
        häzirki_wagt = datetime.now(self.wagt_zolagy)

        ätiýaçlyk_habarlar = [
            f"💡 Şu günler {häzirki_wagt.strftime('%d %B')} senesinde programmirlemekde näme öwrendiň?\n\nHer gün kiçi ädim — uly üstünlikleriň açary! Kod ýazmagyn iň owadan taraplary, hemişe täze zatlar öwrenmekdir 🚀",

            f"🤔 Häzir haýsy tehnologiýa bilen işleýärsiň?\n\nMen şu günler kod gözden geçirýän wagtym şeýle pikir etdim: Iň gowy kod diňe işleýän kod däl, beýlekileriň hem aňsat düşünip bilýän kody! 📝",

            f"⚡ Şu wagt {häzirki_wagt.strftime('%H:%M')} — günüň kod ýazmagyna güýjüň nähili?\n\nKäte iň gowy çözgütler kompýuteri ýapanyňdan soň aklyňa gelýär. Kelle bulaşyk bolsa, gysga gezelenç jadyly bolup biler! 🚶‍♂️"
        ]

        hashtag_lar = "#ProgrammaYazmak #Kod #Höweslendiriş #Öwrenmek"

        howpsuz_esas = random.choice(ätiýaçlyk_habarlar).replace("*", "").replace("_", "").replace("[", "").replace("]", "")

        return f"{howpsuz_esas}\n\n{hashtag_lar}"

    async def kanala_habar_iber(self, habar):
        """Kanala habar ibermek"""
        try:
            await self.bot.send_message(
                chat_id=self.kanal_id,
                text=habar,
                parse_mode='Markdown'
            )
            logger.info("Habar üstünlikli iberildi!")
            return True
        except TelegramError as e:
            logger.error(f"Telegram ýalňyşlygy: {e}")
            return False
        except Exception as e:
            logger.error(f"Habar ibermekde ýalňyşlyk: {e}")
            return False

    async def meýilleşdirilen_mazmun_iber(self):
        """Meýilleşdirilen mazmun ibermek"""
        logger.info("Akylly mazmun döredilýär...")

        häzirki_wagt = datetime.now(self.wagt_zolagy)
        günüň_wagty = self.günüň_wagty()

        # Wagta esaslanan başlyk emojileri
        wagt_emojileri = {
            "ertir": "🌅",
            "günorta": "☀️",
            "ikindi": "🌤️",
            "agşam": "🌙"
        }

        # Mazmun döret
        mazmun = await self.mazmun_döret()

        # Wagt maglumatyny goş
        wagt_str = häzirki_wagt.strftime("%H:%M")
        emoji = wagt_emojileri.get(günüň_wagty, "💻")

        # Soňky habar
        ahyrky_habar = f"{emoji} {mazmun}"

        üstünlik = await self.kanala_habar_iber(ahyrky_habar)
        if üstünlik:
            logger.info(f"Akylly mazmun iberildi! [{wagt_str}]")
        else:
            logger.error("Habar iberilip bilmedi!")

    async def synag_habary(self):
        """Synag habary"""
        print("🤖 Synag üçin tötänleýin mazmun döredilýär...")

        tötänleýin_mazmun = await self.mazmun_döret()

        synag_mazmun = f"""🧪 **SYNAG HABARY** - Bot Işleýär! 🎉

{tötänleýin_mazmun}

---
📅 **Gündelik Programma:**
• 09:00 - Irdenki maslahat
• 12:00 - Günortanlyk mazmun
• 16:00 - Ikindi paýlaşymy
• 21:00 - Agşam jemi

#SynagBot #ProgrammaBot #Kod"""

        üstünlik = await self.kanala_habar_iber(synag_mazmun)
        if üstünlik:
            print("✅ Synag habary üstünlikli iberildi!")
        else:
            print("❌ Synag habary iberilip bilmedi!")

    def habarlary_meýilleşdir(self):
        """Habar meýilleşdirmek"""
        # Türkmenistan wagty bilen meýilleşdirmek
        schedule.every().day.at("09:00").do(lambda: asyncio.create_task(self.meýilleşdirilen_mazmun_iber()))
        schedule.every().day.at("12:00").do(lambda: asyncio.create_task(self.meýilleşdirilen_mazmun_iber()))
        schedule.every().day.at("16:00").do(lambda: asyncio.create_task(self.meýilleşdirilen_mazmun_iber()))
        schedule.every().day.at("21:00").do(lambda: asyncio.create_task(self.meýilleşdirilen_mazmun_iber()))

        logger.info("Habar wagtlary düzüldi!")
        logger.info("Sagatlar: 09:00, 12:00, 16:00, 21:00 (Türkmenistan)")

    async def meýilleşdiriji_işlet(self):
        """Meýilleşdiriji aýlawy"""
        while self.işleýär:
            schedule.run_pending()
            await asyncio.sleep(60)  # Her minut barla

    def flask_programmany_işlet(self):
        """Flask programmasyny işlet"""
        app.run(host='0.0.0.0', port=self.port, debug=False)

    async def işlet(self):
        """Bot işletmek - Railway üçin optimizasiýa edildi"""
        print("🤖 Programmirlemek Boty başlaýar...")

        # Ilkinji synag habary
        await self.synag_habary()

        # Meýilleşdirmeleri düz
        self.habarlary_meýilleşdir()

        print("⏰ Bot meýilleşdirilen habarlar üçin garaşýar...")
        print("📍 Sagatlar: 09:00, 12:00, 16:00, 21:00 (Türkmenistan)")
        print(f"🌐 Flask serweri port {self.port}'da işleýär")

        # Flask'y aýry thread'de işlet
        flask_thread = threading.Thread(target=self.flask_programmany_işlet, daemon=True)
        flask_thread.start()

        # Meýilleşdirijini işlet
        await self.meýilleşdiriji_işlet()

    def dur(self):
        """Bot'y dur"""
        self.işleýär = False
        logger.info("Bot durdurylylyar...")

# Signal handler - Railway üçin
def signal_işleýjisi(signum, frame):
    logger.info(f"Signal {signum} alyndy, bot durdurylylyar...")
    bot_mysaly.dur()
    sys.exit(0)

# El bilen synag funksiýalary
async def häzir_synag_iber():
    """Derrew synag habary iber"""
    bot = ProgrammaBot()
    await bot.synag_habary()

async def tötänleýin_mazmun_iber():
    """Diňe tötänleýin mazmun iber"""
    bot = ProgrammaBot()
    await bot.meýilleşdirilen_mazmun_iber()

async def özüň_habary_iber(habar):
    """Özel habar iber"""
    bot = ProgrammaBot()
    await bot.kanala_habar_iber(habar)

# Global bot mysaly
bot_mysaly = None

if __name__ == "__main__":
    try:
        bot_mysaly = ProgrammaBot()

        # Signal handlers (Railway üçin)
        signal.signal(signal.SIGTERM, signal_işleýjisi)
        signal.signal(signal.SIGINT, signal_işleýjisi)

        # Buýruk setiri argumentleri
        import sys
        if len(sys.argv) > 1:
            if sys.argv[1] == "synag":
                # Synag habary iber
                asyncio.run(häzir_synag_iber())
            elif sys.argv[1] == "tötänleýin":
                # Diňe tötänleýin mazmun iber
                asyncio.run(tötänleýin_mazmun_iber())
            elif sys.argv[1] == "habar" and len(sys.argv) > 2:
                # Özel habar iber
                özüň_habary = " ".join(sys.argv[2:])
                asyncio.run(özüň_habary_iber(özüň_habary))
            else:
                print("Ulanyş:")
                print("python bot.py              - Adaty işletmek")
                print("python bot.py synag        - Synag habary iber")
                print("python bot.py tötänleýin   - Tötänleýin mazmun iber")
                print("python bot.py habar 'Habar mazmuny' - Özel habar iber")
        else:
            # Adaty işletmek (Railway üçin)
            asyncio.run(bot_mysaly.işlet())

    except KeyboardInterrupt:
        print("\n🛑 Bot durdy!")
    except Exception as e:
        logger.error(f"Umumy ýalňyşlyk: {e}")
        print(f"❌ Ýalňyşlyk: {e}")
