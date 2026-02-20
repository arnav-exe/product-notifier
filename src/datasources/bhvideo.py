"""
BH Photo Video Product Scraper
================================
Extracts product name, stock status, and pricing from a bhphotovideo.com page.

Cloudflare bypass — two-pass strategy:
  Pass 1: headless=True (fast, no window). Works on residential IPs.
  Pass 2: headless=False. Used when headless is blocked. On Linux without a
  graphical display (e.g. Raspberry Pi cron job), a virtual framebuffer is
  started automatically — install the OS dependency once with:
      sudo apt-get install xvfb

A persistent browser profile is stored in .browser_profile/ so the
Cloudflare clearance cookie is reused across runs.
"""

import asyncio
import json
import os
import platform
import re
import sys
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

TARGET_URL = (
    "https://www.bhphotovideo.com/c/product/1920305-REG/"
    "lenovo_83n0000aus_legion_go_2_handheld.html"
)

PROFILE_DIR = Path(__file__).parent / ".browser_profile"

_IN_STOCK_SUFFIXES = frozenset({"/InStock", "/LimitedAvailability", "/OnlineOnly", "/BackOrder"})

_JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>\s*(.*?)\s*</script>',
    re.DOTALL | re.IGNORECASE,
)
_LIST_PRICE_LABEL_RE = re.compile(
    r'(?:list\s+price|msrp|manufacturer[\'s]*\s+(?:suggested\s+)?(?:retail\s+)?price'
    r'|regular\s+price|orig(?:inal)?\s+price|was\s*:?|before\s+discount)'
    r'[^$\d]{0,30}\$\s*([\d,]+(?:\.\d{1,2})?)',
    re.IGNORECASE,
)
_DOLLAR_RE = re.compile(r'\$\s*([\d,]+(?:\.\d{1,2})?)')


def _extract_product_jsonld(html):
    for m in _JSONLD_RE.finditer(html):
        try:
            data = json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if isinstance(obj, dict) and obj.get("@type") == "Product":
                return obj
    return None


def _parse_price(raw):
    if raw is None:
        return None
    try:
        return float(str(raw).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None


def _find_list_price(html, current_price):
    for m in _LIST_PRICE_LABEL_RE.finditer(html):
        try:
            candidate = float(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if candidate > current_price:
            return candidate

    # Fall back to scanning all dollar amounts in the pricing container
    idx = html.find('data-selenium="pricingContainer"')
    if idx == -1:
        return None
    start = html.rfind("<", 0, idx)
    if start == -1:
        return None
    region = html[start: start + 2000]
    amounts = [float(m.group(1).replace(",", "")) for m in _DOLLAR_RE.finditer(region)]
    if higher := [v for v in amounts if v > current_price * 1.01]:
        return max(higher)
    return None


def _start_virtual_display():
    """Start an Xvfb virtual framebuffer on headless Linux so a headed browser can open.
    Returns the Display object (call .stop() when done), or None.
    Requires: sudo apt-get install xvfb && pip install pyvirtualdisplay
    """
    if platform.system() != "Linux" or os.environ.get("DISPLAY"):
        return None
    try:
        from pyvirtualdisplay import Display  # noqa: PLC0415
        display = Display(visible=False, size=(1280, 720))
        display.start()
        return display
    except Exception:
        return None


async def _fetch_html(url, headless):
    """Fetch the page; return HTML if the product page loaded, None if Cloudflare blocked."""
    async with AsyncWebCrawler(config=BrowserConfig(
        browser_type="chromium",
        headless=headless,
        use_persistent_context=True,
        user_data_dir=str(PROFILE_DIR),
        verbose=False,
    )) as crawler:
        result = await crawler.arun(url=url, config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            delay_before_return_html=4.0,
            page_timeout=60_000,
            verbose=False,
        ))
    if not result.success:
        return None
    html = result.html or ""
    # A real product page always has JSON-LD; the Cloudflare challenge page does not.
    return html if "application/ld+json" in html else None


async def scrape(url):
    """Scrape a BH Photo product page.
    Returns dict: product_name, is_in_stock, is_on_sale, regular_price, sale_price.
    """
    PROFILE_DIR.mkdir(exist_ok=True)

    html = await _fetch_html(url, headless=True)
    if html is None:
        display = _start_virtual_display()
        try:
            html = await _fetch_html(url, headless=False)
        finally:
            if display:
                display.stop()

    if not html:
        raise RuntimeError(
            "Cloudflare blocked the request in both headless and headed modes.\n"
            "If a browser window appeared, click 'Verify you are human' if "
            "prompted and run the script again."
        )

    if not (product := _extract_product_jsonld(html)):
        raise RuntimeError("No schema.org/Product JSON-LD found. The page structure may have changed.")

    offers = product.get("offers", {})
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        offers = {}

    if (current_price := _parse_price(offers.get("price"))) is None:
        raise RuntimeError(f"Could not parse price: {offers.get('price')!r}")

    list_price = _find_list_price(html, current_price)

    return {
        "product_name":  product.get("name"),
        "is_in_stock":   any(offers.get("availability", "").endswith(s) for s in _IN_STOCK_SUFFIXES),
        "is_on_sale":    list_price is not None,
        "regular_price": list_price if list_price is not None else current_price,
        "sale_price":    current_price,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    url = sys.argv[1] if len(sys.argv) > 1 else TARGET_URL
    print(f"Scraping: {url}")
    print("-" * 60)

    try:
        p = asyncio.run(scrape(url))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    regular, sale = p["regular_price"], p["sale_price"]
    print(f"Product Name  : {p['product_name']}")
    print(f"In Stock      : {p['is_in_stock']}")
    print(f"On Sale       : {p['is_on_sale']}")
    print(f"Regular Price : {'${:.2f}'.format(regular) if regular is not None else 'N/A'}")
    print(f"Sale Price    : {'${:.2f}'.format(sale)    if sale    is not None else 'N/A'}")


if __name__ == "__main__":
    main()
