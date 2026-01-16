import requests

BOT_TOKEN = "BOT_TOKEN"

updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates").json()
print(updates)
