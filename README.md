# SkyNewsBot 🌤️📡

Malaysia’s real-time IRC newsroom—powered by RSS! SkyNewsBot connects to your IRC channel and posts hourly updates from Bernama and Astro Awani.

## ⚙️ Features
- 🔁 Hourly automated news updates
- 📰 Dual RSS sources
- 💬 IRC connectivity with channel delivery

## 📦 Setup

### 1. Clone & Install
```bash
git clone https://github.com/sky/SkyNewsBot.git
cd SkyNewsBot
pip install -r requirements.txt

### 2. Configure
Edit news_rss_bot.py:

IRC server (SERVER)

Port (PORT)

Channel name (CHANNEL)

### 3. Run the Bot
bash
python news_dual_rss_bot.py