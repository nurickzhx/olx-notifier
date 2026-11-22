#!/usr/bin/env python3
"""olx_notifier.py

Telegram‑bot, который периодически проверяет выбранную категорию OLX и присылает
сообщения о новых объявлениях в личный чат.
"""

import json, hashlib, time
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse

# ==== НАСТРОЙКИ =============================================================
# Telegram credentials (set as env vars)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Operational flags
ENABLED = os.getenv("ENABLED", "true").lower() == "true"

# Path to store seen ad IDs
SEEN_FILE = "seen_ids.json"

# Optional: custom OLX URL (single city+keyword). If set, overrides city/keyword generation.
CUSTOM_URL = os.getenv("CUSTOM_URL", "").strip()

# Load list of city slugs (Kazakhstan). Either from CITIES env (comma‑separated) or from cities.txt file.
CITIES_ENV = os.getenv("CITIES")
if CITIES_ENV:
    CITY_LIST = [c.strip() for c in CITIES_ENV.split(",") if c.strip()]
else:
    try:
        with open("cities.txt", "r", encoding="utf-8") as f:
            CITY_LIST = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        CITY_LIST = []  # fallback empty list

# Load keywords (search terms). From KEYWORDS env (comma‑separated) or default list.
KEYWORDS_ENV = os.getenv("KEYWORDS")
if KEYWORDS_ENV:
    KEYWORD_LIST = [kw.strip() for kw in KEYWORDS_ENV.split(",") if kw.strip()]
else:
    KEYWORD_LIST = ["iphone", "playstation 5", "компьютер", "macbook"]

# Build list of URLs to scrape
if CUSTOM_URL:
    URL_LIST = [CUSTOM_URL]
else:
    URL_LIST = []
    for city in CITY_LIST:
        for kw in KEYWORD_LIST:
            encoded = urllib.parse.quote_plus(kw)
            url = f"https://www.olx.kz/{city}/search?search%5Bdescription%5D={encoded}"
            URL_LIST.append(url)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.olx.kz/",
    "Connection": "keep-alive",
})
# ===========================================================================

def load_seen() -> set:
    """Загружает набор уже виденных идентификаторов объявлений."""
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen(seen: set) -> None:
    """Сохраняет набор идентификаторов в файл."""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

def fetch_ads(url: str) -> list:
    """Получает список объявлений со страницы URL."""
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            print(f"[WARN] 403 Forbidden for {url} – skip")
            return []
        raise
    soup = BeautifulSoup(resp.text, "html.parser")
    ads = []
    for link_el in soup.select("a[data-testid='listing-ad']"):
        ad_url = link_el.get("href")
        title_el = link_el.select_one("h6")
        title = title_el.get_text(strip=True) if title_el else "(без заголовка)"
        price_el = link_el.select_one("[data-testid='ad-price']")
        price = price_el.get_text(strip=True) if price_el else "(без цены)"
        ad_id = hashlib.sha256(ad_url.encode()).hexdigest()
        ads.append({"id": ad_id, "title": title, "price": price, "url": ad_url})
    # небольшая случайная пауза, чтобы не перегружать сайт
    import random, time
    time.sleep(random.uniform(1.0, 3.0))
    return ads
    """Получает список объявлений со страницы URL."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    ads = []
    for link_el in soup.select("a[data-testid='listing-ad']"):
        ad_url = link_el.get("href")
        title_el = link_el.select_one("h6")
        title = title_el.get_text(strip=True) if title_el else "(без заголовка)"
        price_el = link_el.select_one("[data-testid='ad-price']")
        price = price_el.get_text(strip=True) if price_el else "(без цены)"
        ad_id = hashlib.sha256(ad_url.encode()).hexdigest()
        ads.append({"id": ad_id, "title": title, "price": price, "url": ad_url})
    return ads

def send_telegram(ad: dict) -> None:
    """Отправляет одно объявление в Telegram‑чат."""
    text = (
        f"🆕 Новое объявление\n"
        f"🔹 {ad['title']}\n"
        f"💰 {ad['price']}\n"
        f"🔗 {ad['url']}"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[WARN] Ошибка отправки в Telegram: {e}")

def main():
    if not ENABLED:
        print("Bot disabled via ENABLED flag.")
        return
    # Interval in seconds (default 120 s ≈ 2 min)
    INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "120"))
    while True:
        seen = load_seen()
        for target_url in URL_LIST:
            for ad in fetch_ads(target_url):
                if ad["id"] not in seen:
                    send_telegram(ad)
                    seen.add(ad["id"])
        save_seen(seen)
        print(f"[INFO] Cycle completed, sleeping {INTERVAL_SECONDS}s…")
        time.sleep(INTERVAL_SECONDS)

    if not ENABLED:
        print("Bot disabled via ENABLED flag.")
        return
    seen = load_seen()
    for target_url in URL_LIST:
        for ad in fetch_ads(target_url):
            if ad["id"] not in seen:
                send_telegram(ad)
                seen.add(ad["id"])
    save_seen(seen)

if __name__ == "__main__":
    main()
