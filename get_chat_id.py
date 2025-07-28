import requests

BOT_TOKEN = "8488579521:AAHXBZQxNNsRUmNBNaDZLECaiKIA7eTTh4Y"

updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates").json()
print(updates)
