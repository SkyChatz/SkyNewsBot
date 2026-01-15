"""
SkyNewsBot - Malaysia IRC RSS News Aggregator 📰🇲🇾

Author: Sky
Version: 2.0.0
License: MIT
Description:
    SkyNewsBot connects to an IRC channel and automatically posts hourly headlines
    from Bernama and Astro Awani using their RSS feeds.

    Designed for Malaysian IRC communities who crave timely news.

Repository: https://github.com/sky/SkyNewsBot
"""

import socket
import time
import threading
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

# --- IRC Settings ---
SERVER = "ipv6.skychatz.org"
PORT = 7000
NICK = "SkyNewsBot"
USER = "newsuser"
REALNAME = "Malaysia News Bot"
CHANNEL = "#SkyChatz"

# --- Configuration ---
RATE_LIMIT_DELAY = 2.0  # seconds between messages to avoid flooding
RECONNECT_DELAY = 30  # seconds before attempting reconnect
NEWS_UPDATE_HOUR = 0  # Post news at minute 0 of each hour

class SkyNewsBot:
    def __init__(self):
        self.irc = None
        self.connected = False
        self.last_posted_hour = -1
        self.scraper = cloudscraper.create_scraper()
        
    def connect(self):
        """Establish connection to IRC server"""
        try:
            self.irc = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.irc.settimeout(300)  # 5 minute timeout
            self.irc.connect((SERVER, PORT))
            self.send(f"NICK {NICK}")
            self.send(f"USER {USER} 0 * :{REALNAME}")
            print(f"[✓] Connected to {SERVER}:{PORT}")
            return True
        except Exception as e:
            print(f"[✗] Connection failed: {e}")
            return False
    
    def send(self, msg):
        """Send message to IRC server with logging"""
        print(f"[→] {msg.strip()}")
        try:
            self.irc.sendall((msg + "\r\n").encode("utf-8"))
        except Exception as e:
            print(f"[✗] Send failed: {e}")
            self.connected = False
    
    def fetch_bernama_headlines(self):
        """Fetch latest Bernama headlines"""
        try:
            response = self.scraper.get(
                "https://www.bernama.com/en/rssfeed.php", 
                timeout=10
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item", limit=5)
            
            headlines = []
            for item in items:
                title = item.title.text.strip()[:150]  # Limit length
                link = item.link.text.strip()
                headlines.append(f"Bernama: {title} - {link}")
            return headlines
            
        except Exception as e:
            print(f"[✗] Bernama RSS error: {e}")
            return [f"[✗] Bernama RSS error: {e}"]
    
    def fetch_astro_headlines(self):
        """Fetch latest Astro Awani headlines"""
        try:
            response = self.scraper.get(
                "https://rss.astroawani.com/rss/latest/public", 
                timeout=10
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item", limit=5)
            
            headlines = []
            for item in items:
                title = item.title.text.strip()[:150]  # Limit length
                link = item.link.text.strip()
                headlines.append(f"Astro Awani: {title} - {link}")
            return headlines
            
        except Exception as e:
            print(f"[✗] Astro Awani RSS error: {e}")
            return [f"[✗] Astro Awani RSS error: {e}"]
    
    def post_headlines(self):
        """Post headlines to IRC channel with rate limiting"""
        if not self.connected:
            return
        
        current_time = datetime.now()
        if current_time.hour == self.last_posted_hour:
            return
        
        try:
            self.send(f"PRIVMSG {CHANNEL} :🕒 Hourly Update: Bernama & Astro Awani")
            time.sleep(RATE_LIMIT_DELAY)
            
            # Fetch and post Bernama headlines
            bernama = self.fetch_bernama_headlines()
            for headline in bernama:
                self.send(f"PRIVMSG {CHANNEL} :{headline}")
                time.sleep(RATE_LIMIT_DELAY)
            
            # Fetch and post Astro Awani headlines
            astro = self.fetch_astro_headlines()
            for headline in astro:
                self.send(f"PRIVMSG {CHANNEL} :{headline}")
                time.sleep(RATE_LIMIT_DELAY)
            
            self.send(f"PRIVMSG {CHANNEL} :✅ News synced at {current_time:%H:%M}.")
            time.sleep(RATE_LIMIT_DELAY)
            
            self.last_posted_hour = current_time.hour
            print(f"[✓] Posted news for hour {current_time.hour}:00")
            
        except Exception as e:
            print(f"[✗] Failed to post headlines: {e}")
    
    def run(self):
        """Main bot loop"""
        print("[🚀] SkyNewsBot starting...")
        
        while True:
            try:
                if not self.connected:
                    if self.connect():
                        self.connected = True
                    else:
                        print(f"[⏳] Reconnecting in {RECONNECT_DELAY} seconds...")
                        time.sleep(RECONNECT_DELAY)
                        continue
                
                # Receive and process IRC messages
                try:
                    data = self.irc.recv(2048).decode("utf-8", errors="ignore")
                    if not data:
                        print("[!] Connection closed by server")
                        self.connected = False
                        continue
                        
                    for line in data.strip().split("\r\n"):
                        if line:
                            print(f"[←] {line}")
                            
                            if line.startswith("PING"):
                                ping_id = line.split("PING ")[1]
                                self.send(f"PONG {ping_id}")
                                
                            elif f" 001 {NICK} " in line:
                                self.send(f"JOIN {CHANNEL}")
                                self.send(f"PRIVMSG {CHANNEL} :👋 SkyNewsBot v2.0 is online. Hourly news updates active.")
                                
                            # Check for hour change
                            current_minute = datetime.now().minute
                            if current_minute == NEWS_UPDATE_HOUR:
                                threading.Thread(target=self.post_headlines, daemon=True).start()
                                
                except socket.timeout:
                    # Send PING to keep connection alive
                    self.send(f"PING :{int(time.time())}")
                    continue
                    
                except Exception as e:
                    print(f"[!] Receive error: {e}")
                    self.connected = False
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n[✋] Shutting down...")
                if self.irc:
                    self.send(f"QUIT :SkyNewsBot shutting down")
                    self.irc.close()
                break
            except Exception as e:
                print(f"[!] Unexpected error: {e}")
                self.connected = False
                time.sleep(RECONNECT_DELAY)

if __name__ == "__main__":
    bot = SkyNewsBot()
    bot.run()
