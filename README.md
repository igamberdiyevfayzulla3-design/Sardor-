# 🎓 Ziyrak Study Bot

O'zbek tilida AI-powered o'quv yordamchisi Telegram boti.

## Funksiyalar

| Modul | Tavsif |
|-------|--------|
| 🧠 AI Tutor | Istalgan fandan savollarga AI javob |
| 📝 Test Generator | Matndan avtomatik test yaratish |
| 🎯 Quiz Mode | Fanlar bo'yicha interaktiv quiz |
| 📋 Konspekt | Katta matndan qisqa konspekt |
| 🃏 Flashcard | Yodlash uchun kartalar |
| 🌐 Tarjima | UZ ↔ EN ↔ RU tarjima |
| ⚗️ Formulalar | Matematika/Fizika/Kimyo formulalari |

---

## O'rnatish

### 1. Tokenlarni oling

**Telegram Bot Token:**
1. Telegramda @BotFather ga boring
2. `/newbot` yozing
3. Bot nomi va username bering
4. Token nusxa oling

**Anthropic API Key:**
1. https://console.anthropic.com saytiga kiring
2. API Keys bo'limida yangi kalit yarating

---

### 2. O'rnatish

```bash
# Papkaga kiring
cd ziyrak_bot

# Virtual muhit yarating (tavsiya etiladi)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Kutubxonalarni o'rnating
pip install -r requirements.txt

# .env fayl yarating
cp .env.example .env
```

### 3. .env faylni to'ldiring

```env
BOT_TOKEN=1234567890:ABCDEFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. Botni ishga tushiring

```bash
python bot.py
```

---

## Server (VPS)ga deploy qilish

### systemd service (Linux)

```bash
sudo nano /etc/systemd/system/ziyrak.service
```

```ini
[Unit]
Description=Ziyrak Study Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ziyrak_bot
Environment=PATH=/home/ubuntu/ziyrak_bot/venv/bin
ExecStart=/home/ubuntu/ziyrak_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ziyrak
sudo systemctl start ziyrak
sudo systemctl status ziyrak
```

---

## Buyruqlar

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni boshlash |
| `/menu` | Bosh menyu |

---

## Texnologiyalar

- **Python 3.10+**
- **aiogram 3.x** — Telegram Bot framework
- **Anthropic Claude** — AI API
- **python-dotenv** — Muhit o'zgaruvchilari
