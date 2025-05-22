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
