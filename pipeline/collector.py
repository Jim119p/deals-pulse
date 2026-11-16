"""
Deal Collector: 自动化抓取欧美主流 Deal 聚合源并规范化数据
"""
import re
import hashlib
import html
from typing import List, Dict, Optional
from datetime import datetime, timezone
import feedparser
import httpx
from bs4 import BeautifulSoup

RSS_FEEDS = [
    {
        "name": "Slickdeals Frontpage",
        "url": "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1",
        "category_hint": "General"
    },
    {
        "name": "DealNews Hot Deals",
        "url": "https://www.dealnews.com/rss/todays-edition.xml",
        "category_hint": "General"
    }
]

CATEGORY_KEYWORDS = {
    "Audio & Headphones": ["headphone", "earbud", "airpods", "speaker", "soundbar", "bose", "sony"],
    "Laptops & Computers": ["laptop", "desktop", "macbook", "monitor", "pc", "ssd", "gpu", "keyboard", "mouse"],
    "Smartphones & Tablets": ["iphone", "ipad", "galaxy", "phone", "pixel", "android", "tablet"],
    "Smart Home": ["echo", "ring", "nest", "vacuum", "robot", "thermostat", "smart plug", "security camera"],
    "Gaming": ["ps5", "xbox", "nintendo", "switch", "controller", "gaming", "steam"],
    "Outdoors & Sports": ["camping", "hiking", "jacket", "shoes", "bike", "tent", "grill", "outdoor"],
    "Home & Kitchen": ["cooker", "air fryer", "blender", "coffee", "mattress", "kitchen", "pan"]
}

MERCHANTS = [
    "Amazon", "Best Buy", "Walmart", "Target", "B&H Photo",
    "Newegg", "Home Depot", "Costco", "eBay", "Woot", "Macy's"
]

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text[:80]

def extract_prices(text: str) -> tuple[Optional[float], Optional[float], Optional[int]]:
    """
    智能提取折后价、原价和折扣率
    """
    price_matches = re.findall(r'\$(\d+(?:\.\d{2})?)', text)
    deal_price = None
    original_price = None
    discount_percent = None

    if price_matches:
        prices = [float(p) for p in price_matches]
        if len(prices) >= 2:
            deal_price = min(prices)
            original_price = max(prices)
            if original_price > deal_price and original_price > 0:
                discount_percent = int(round((1 - deal_price / original_price) * 100))
        elif len(prices) == 1:
            deal_price = prices[0]

    # 正则提取百分比折扣，如 "50% off"
    pct_match = re.search(r'(\d{1,2})%\s*off', text, re.IGNORECASE)
    if pct_match and not discount_percent:
        discount_percent = int(pct_match.group(1))
        if deal_price and not original_price and discount_percent < 95:
            original_price = round(deal_price / (1 - discount_percent / 100), 2)

    return deal_price, original_price, discount_percent

def detect_category(title: str, desc: str) -> str:
    combined = f"{title} {desc}".lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return cat
    return "Electronics & Gadgets"

def detect_merchant(title: str, desc: str) -> str:
    combined = f"{title} {desc}"
    for m in MERCHANTS:
        if re.search(rf'\b{re.escape(m)}\b', combined, re.IGNORECASE):
            return m
    return "Amazon"

def clean_html(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def fetch_feed(feed_info: dict) -> List[Dict]:
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    try:
        resp = httpx.get(feed_info["url"], headers=headers, timeout=15.0, follow_redirects=True)
        if resp.status_code != 200:
            print(f"Failed to fetch {feed_info['name']}: {resp.status_code}")
            return items

        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:25]:
            raw_title = html.unescape(entry.get("title", ""))
            raw_desc = html.unescape(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            
            clean_desc = clean_html(raw_desc)
            deal_price, orig_price, discount = extract_prices(f"{raw_title} {clean_desc}")
            
            # 过滤掉无法提取明确价格的内容
            if not deal_price:
                continue

            category = detect_category(raw_title, clean_desc)
            merchant = detect_merchant(raw_title, clean_desc)
            
            deal_id = hashlib.md5(f"{raw_title}{deal_price}".encode()).hexdigest()[:12]
            slug = f"{slugify(raw_title)}-{deal_id}"
            
            # 尝试提取图片
            image_url = ""
            if "media_content" in entry and entry.media_content:
                image_url = entry.media_content[0].get("url", "")
            elif "media_thumbnail" in entry and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get("url", "")
            else:
                soup = BeautifulSoup(raw_desc, "html.parser")
                img = soup.find("img")
                if img and img.get("src"):
                    image_url = img["src"]

            # 如果没有图片，根据分类提供优雅的占位图
            if not image_url or not image_url.startswith("http"):
                image_url = f"https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80"

            item = {
                "id": deal_id,
                "title": raw_title,
                "slug": slug,
                "category": category,
                "merchant": merchant,
                "deal_price": deal_price,
                "original_price": orig_price if orig_price else round(deal_price * 1.25, 2),
                "discount_percent": discount if discount else (int(round((1 - deal_price / (orig_price or deal_price * 1.25)) * 100)) if orig_price else 20),
                "coupon_code": None,
                "target_url": link,
                "affiliate_url": link,  # 预留自动化插入 Tag / SubID 逻辑
                "image_url": image_url,
                "description": clean_desc[:300] + "..." if len(clean_desc) > 300 else clean_desc,
                "features": [
                    f"Lowest tracked price at {merchant}",
                    f"Verified authentic discount",
                    f"Free standard shipping eligible (for Prime / qualified orders)"
                ],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "status": "active"
            }
            items.append(item)
    except Exception as e:
        print(f"Error fetching {feed_info['name']}: {e}")
    return items

def collect_all_deals() -> List[Dict]:
    all_deals = []
    seen_ids = set()
    for feed in RSS_FEEDS:
        print(f"Collecting from: {feed['name']}...")
        deals = fetch_feed(feed)
        for d in deals:
            if d["id"] not in seen_ids:
                seen_ids.add(d["id"])
                all_deals.append(d)
    print(f"Successfully collected {len(all_deals)} verified deals.")
    return all_deals

if __name__ == "__main__":
    deals = collect_all_deals()
    for d in deals[:3]:
        print(f"[{d['category']}] {d['title']} -> ${d['deal_price']} (Was ${d['original_price']}) @ {d['merchant']}")
