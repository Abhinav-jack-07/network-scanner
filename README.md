# 🕵️‍♂️ Simple Network Scanner

A simple Python-based ARP network scanner using Scapy. It scans a local subnet and lists active devices with their IP and MAC addresses. Requires Python 3 and admin privileges.

## 📦 Requirements
- Python 3
- scapy (`pip install scapy`)
- Run as root/administrator

## 💻 Usage
```bash
sudo python scanner.py
```

Edit the IP range in the script:
```python
target_ip_range = "192.168.1.0/24"
```

## ⚠️ Disclaimer
For educational use only. Do not scan networks you do not own or have permission to scan.

## 🤖 WhatsApp AI Chatbot (optional)
A minimal FastAPI-based WhatsApp webhook + AI responder lives in `whatsapp_bot/`. It supports:
- Webhook verification and signature checks
- FAQ responses from `whatsapp_bot/faq.json`
- AI replies with OpenAI Chat Completions
- Opt-in/opt-out and human handoff keywords
- Basic rate limiting and health checks

### Setup
1. Create a WhatsApp Business Account and app, then enable the WhatsApp Cloud API.
2. Copy the environment template:
   ```bash
   cp whatsapp_bot/.env.example whatsapp_bot/.env
   ```
3. Fill in the required credentials in `whatsapp_bot/.env`.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the server:
   ```bash
   uvicorn whatsapp_bot.app:app --host 0.0.0.0 --port 8000
   ```
6. Configure your webhook URL to `https://<public-domain>/webhook` and verify using `WHATSAPP_VERIFY_TOKEN`.

### Compliance & operations
- Respect opt-in/opt-out keywords and WhatsApp policy requirements.
- Store secrets in environment variables or a secrets manager.
- Review data retention rules for your region and industry before production use.
