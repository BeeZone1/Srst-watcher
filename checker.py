import os
import requests
from bs4 import BeautifulSoup
import json

URL = "https://www.nasegalanterie.cz/vyroba-prize/"
STORAGE_FILE = "known_products.json"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing Telegram config")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def load_known_products():
    if not os.path.exists(STORAGE_FILE):
        return set()
    with open(STORAGE_FILE, "r") as f:
        return set(json.load(f))

def save_known_products(ids):
    with open(STORAGE_FILE, "w") as f:
        json.dump(list(ids), f)

def fetch_products():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(".products .product")  # обёртка карточек
    products = []
    for item in items:
        link_tag = item.select_one("a.perex")
        if not link_tag:
            continue
        href = link_tag["href"]
        name = link_tag.get_text(strip=True)
        product_id = href.split("/")[-2]  # id из URL
        full_url = "https://www.nasegalanterie.cz" + href
        products.append({
            "id": product_id,
            "name": name,
            "url": full_url
        })
    return products

def main():
    known_ids = load_known_products()
    products = fetch_products()
    new_products = [p for p in products if p["id"] not in known_ids]

    if new_products:
        print(f"Found {len(new_products)} new product(s)")
        for p in new_products:
            message = f"🧵 <b>New product:</b> <a href=\"{p['url']}\">{p['name']}</a>"
            send_telegram_message(message)

        all_ids = known_ids.union(p["id"] for p in products)
        save_known_products(all_ids)
    else:
        print("No new products")

if __name__ == "__main__":
    main()
