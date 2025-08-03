import asyncio
import json
import os
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# ========= НАСТРОЙКИ =========
START_URL = "https://www.nasegalanterie.cz/vyroba-prize/?order=name"
DATA_FILE = "products.json"
BOT_TOKEN =  os.getenv("BOT_TOKEN")
CHAT_IDS = ["139262632", "513144824"]  # Telegram ID получателей

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
    print(f"💾 Сохранено {len(products)} товаров в базе.")

# ========= ПАРСИНГ ВСЕХ СТРАНИЦ =========
async def fetch_all_products():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = START_URL
        products = []
        page_num = 1

        while True:
            print(f"🔄 Загружаем страницу {page_num}: {url}")
            await page.goto(url)
            await page.wait_for_selector("div.category-content-wrapper", timeout=20000)
            html = await page.content()

            soup = BeautifulSoup(html, "html.parser")
            wrapper = soup.select_one("div.category-content-wrapper")

            if not wrapper:
                print("❌ Контейнер товаров не найден.")
                break

            page_products = []
            for item in wrapper.select("div.product"):
                name_tag = item.select_one("a.name span[data-micro='name']")
                name = name_tag.get_text(strip=True) if name_tag else "Без названия"

                link_tag = item.select_one("a.name")
                url_item = "https://www.nasegalanterie.cz" + link_tag["href"] if link_tag else ""

                price_tag = item.select_one(".price-final strong")
                price = price_tag.get_text(strip=True) if price_tag else "N/A"

                page_products.append({
                    "id": name,  # используем название как ID
                    "name": name,
                    "url": url_item,
                    "price": price
                })

            print(f"📦 Найдено товаров на странице: {len(page_products)}")
            products.extend(page_products)

            # Проверяем, есть ли кнопка "Next"
            next_button = soup.select_one("a.next.pagination-link[data-testid='linkNextPage']")
            if next_button and next_button.get("href"):
                url = "https://www.nasegalanterie.cz" + next_button["href"]
                page_num += 1
            else:
                print("✅ Последняя страница достигнута.")
                break

        await browser.close()
        print(f"📊 Всего собрано товаров: {len(products)}")
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

# ========= ЛОГИКА =========
async def main():
    current_products = await fetch_all_products()
    previous_products = load_previous_products()

    prev_keys = {p["id"] for p in previous_products}
    curr_keys = {p["id"] for p in current_products}

    print("📂 Предыдущие товары:", prev_keys)
    print("📂 Текущие товары:", curr_keys)

    new_items = [p for p in current_products if p["id"] not in prev_keys]

    if not previous_products:
        print("📂 База пуста — создаём новую.")
        save_products(current_products)
        return

    if not new_items:
        print("✅ Новых товаров нет.")
    else:
        print(f"🆕 Найдено новых товаров: {len(new_items)}")
        message = "🆕 *Новые товары:*\n\n"
        for p in new_items:
            message += f"• {p['name']} – {p['price']}\n{p['url']}\n\n"
        send_telegram_message(message)

    save_products(current_products)

if __name__ == "__main__":
    asyncio.run(main())
