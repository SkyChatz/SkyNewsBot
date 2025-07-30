"""
SkyNewsBot - Malaysia IRC RSS News Aggregator 📰🇲🇾

Author: Sky
Version: 1.0.0
License: MIT
Description:
    SkyNewsBot connects to an IRC channel and automatically posts hourly headlines
    from Bernama and Astro Awani using their RSS feeds.

    Designed for Malaysian IRC communities who crave timely news.

Repository: https://github.com/sky/SkyNewsBot
"""

import socket
import time
import cloudscraper
from bs4 import BeautifulSoup

# --- IRC Settings ---
SERVER = "ipv6.skychatz.org"
PORT = 7000
NICK = "SkyNewsBot"
USER = "newsuser"
REALNAME = "Malaysia News Bot"
CHANNEL = "#SkyChatz"

# --- IRC Socket ---
irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
irc.connect((SERVER, PORT))

def send(msg):
    print(f"[→] {msg.strip()}")
    irc.sendall((msg + "\r\n").encode("utf-8"))

# --- IRC Handshake ---
send(f"NICK {NICK}")
send(f"USER {USER} 0 * :{REALNAME}")

# --- Fetch Bernama RSS headlines ---
def fetch_bernama_headlines():
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://www.bernama.com/en/rssfeed.php", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item", limit=5)
        return [f"Bernama: {item.title.text.strip()} - {item.link.text.strip()}" for item in items]
    except Exception as e:
        return [f"[✗] Bernama RSS error: {e}"]

# --- Fetch Astro Awani RSS headlines ---
def fetch_astro_headlines():
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get("https://rss.astroawani.com/rss/latest/public", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item", limit=5)
        return [f"Astro Awani: {item.title.text.strip()} - {item.link.text.strip()}" for item in items]
    except Exception as e:
        return [f"[✗] Astro Awani RSS error: {e}"]

# --- IRC Event Loop with Hourly Refresh ---
joined = False
last_hour = -1

try:
    while True:
        response = irc.recv(2048).decode("utf-8", errors="ignore")
        for line in response.strip().split("\r\n"):
            print(f"[←] {line}")

            if line.startswith("PING"):
                ping_id = line.split("PING ")[1]
                send(f"PONG {ping_id}")

            elif f" 001 {NICK} " in line and not joined:
                send(f"JOIN {CHANNEL}")
                joined = True
                send(f"PRIVMSG {CHANNEL} :👋 SkyNewsBot is online. Hourly news updates active.")

        current_hour = time.localtime().tm_hour
        current_minute = time.localtime().tm_min

        if current_minute == 0 and current_hour != last_hour:
            last_hour = current_hour

            bernama = fetch_bernama_headlines()
            astro = fetch_astro_headlines()

            send(f"PRIVMSG {CHANNEL} :🕒 Hourly Update: Bernama & Astro Awani")

            for headline in bernama:
                send(f"PRIVMSG {CHANNEL} :{headline}")
            for headline in astro:
                send(f"PRIVMSG {CHANNEL} :{headline}")

            send(f"PRIVMSG {CHANNEL} :✅ News synced at {current_hour:02d}:00.")

            time.sleep(60)
        else:
            time.sleep(15)
except KeyboardInterrupt:
    print("[✋] Bot stopped.")
    irc.close()
