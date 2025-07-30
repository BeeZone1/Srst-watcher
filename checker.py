# import os
# import requests

# # ========= НАСТРОЙКИ =========
# BOT_TOKEN = os.getenv("BOT_TOKEN")  # GitHub Secret
# CHAT_IDS = ["139262632"]  # Telegram ID получателей , "513144824"

# # ========= TELEGRAM =========
# def send_telegram_message(text):
#     for chat_id in CHAT_IDS:
#         resp = requests.post(
#             f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
#             json={"chat_id": chat_id, "text": text}
#         )
#         if resp.status_code == 200:
#             print(f"✅ Сообщение отправлено {chat_id}")
#         else:
#             print(f"⚠ Ошибка отправки: {resp.text}")

# # ========= ОСНОВНОЙ ЗАПУСК =========
# def main():
#     print("📨 Отправляем тестовое сообщение...")
#     send_telegram_message("ПРИВЕТ")

# if __name__ == "__main__":
#     main()

import asyncio
import json
import os
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ========= НАСТРОЙКИ =========
URL = "https://www.nasegalanterie.cz/vyroba-prize/?order=name"
DATA_FILE = "products.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")  # GitHub Secret
CHAT_IDS = ["139262632"]  # Telegram ID получателей , "98765432"

# ========= ХРАНЕНИЕ =========
def load_previous_products():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_products(products):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"💾 Сохранено {len(products)} товаров.")

# ========= ПАРСИНГ =========
async def fetch_products():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"🔄 Загружаем: {URL}")
        await page.goto(URL)
        await page.wait_for_selector("[data-testid='linkLastPage']", timeout=15000)

        # Ссылка на последнюю страницу
        last_page_link = await page.get_attribute("[data-testid='linkLastPage']", "href")
        if not last_page_link:
            print("❌ Не нашли последнюю страницу")
            await browser.close()
            return []

        last_url = "https://www.nasegalanterie.cz" + last_page_link
        print(f"➡ Переходим: {last_url}")
        await page.goto(last_url)
        await page.wait_for_selector("div.category-content-wrapper", timeout=20000)

        html = await page.content()
        await browser.close()

    soup = BeautifulSoup(html, "html.parser")
    wrapper = soup.select_one("div.category-content-wrapper")
    if not wrapper:
        print("❌ Контейнер товаров не найден.")
        return []

    products = []
    for item in wrapper.select("div.product"):
        name_tag = item.select_one("a.name span[data-micro='name']")
        name = name_tag.get_text(strip=True) if name_tag else "Без названия"

        link_tag = item.select_one("a.name")
        url = "https://www.nasegalanterie.cz" + link_tag["href"] if link_tag else ""

        price_tag = item.select_one(".price-final strong")
        price = price_tag.get_text(strip=True) if price_tag else "N/A"

        prod_id = item.get("data-micro-product-id", "")

        products.append({
            "id": prod_id,
            "name": name,
            "url": url,
            "price": price
        })

    print(f"📦 Найдено товаров: {len(products)}")
    return products

# ========= TELEGRAM =========
def send_telegram_message(text):
    for chat_id in CHAT_IDS:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": False}
        )
        if resp.status_code == 200:
            print(f"✅ Сообщение отправлено {chat_id}")
        else:
            print(f"⚠ Ошибка Telegram: {resp.text}")

# ========= ОСНОВНАЯ ЛОГИКА =========
async def main():
    current_products = await fetch_products()
    previous_products = load_previous_products()

    if not previous_products:
        print("📂 База пуста, создаём новую...")
        save_products(current_products)
        return

    prev_ids = {p["id"] for p in previous_products}
    new_items = [p for p in current_products if p["id"] not in prev_ids]

    if not new_items:
        print("✅ Новых товаров нет.")
    else:
        print(f"🆕 Новые товары: {len(new_items)}")
        message = "🆕 *Новые товары:*\n\n"
        for p in new_items:
            message += f"• {p['name']} – {p['price']}\n{p['url']}\n\n"
        send_telegram_message(message)

    save_products(current_products)

if __name__ == "__main__":
    asyncio.run(main())
