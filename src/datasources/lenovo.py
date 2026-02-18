import asyncio
import json
import re
import sys

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


URL = "https://www.lenovo.com/us/en/p/handheld/legion-go-gen-2/83n0000aus"

IN_STOCK_URIS = frozenset({
    "http://schema.org/InStock",
    "https://schema.org/InStock",
    "http://schema.org/LimitedAvailability",
    "https://schema.org/LimitedAvailability",
})

NOT_IN_STOCK_RE = re.compile(
    r"available\s+soon|coming\s+soon|notify\s+me|out\s+of\s+stock"
    r"|sold\s+out|no\s+longer\s+available|unavailable",
    re.IGNORECASE,
)
EST_VALUE_RE = re.compile(r"Est\s+Value[^$]*\$([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
PERCENT_OFF_RE   = re.compile(r"\d+\s*%\s*off", re.IGNORECASE)

SCAN_WINDOW = 1000  # product info usually appears within first 400 chars of <main> - restrict around that

INJECTED_RE = re.compile(
    r'<script[^>]+type=["\']text/x-scraper-data["\'][^>]*>([\s\S]*?)</script>',
    re.IGNORECASE,
)

_JS = """
(async () => {
    Array.from(document.querySelectorAll('button, [role="button"]')).forEach(btn => {
        const lbl = (btn.getAttribute('aria-label') || btn.textContent || '')
                    .toLowerCase().trim();
        if (lbl.includes('close') || lbl === 'x' || lbl === '\u00d7') {
            try { btn.click(); } catch (_) {}
        }
    });

    // wait for popups and smartsales.lenovo.com price widget to render
    await new Promise(r => setTimeout(r, 1500));

    const out = { name: null, price: null, availability: null, mainText: '' };

    for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
        let d;
        try { d = JSON.parse(s.textContent); } catch (_) { continue; }
        // get Product block from pdp
        if (d['@type'] === 'Product' && d.offers) {
            out.name         = d.name                ?? null;
            out.price        = d.offers.price        ?? null;
            out.availability = d.offers.availability ?? null;
            break;
        }
    }

    // exclude header/footer/popup text (sometimes returns other product prices)
    const mainEl = document.querySelector('main');
    out.mainText = mainEl ? mainEl.innerText : document.body.innerText;

    const tag = document.createElement('script');
    tag.type        = 'text/x-scraper-data';
    tag.textContent = JSON.stringify(out);
    document.body.appendChild(tag);
})();
"""


def _parse_price(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


async def scrape(url) -> dict:
    browser_cfg = BrowserConfig(
        browser_type="undetected",  # avoid bot tedection
        headless=True,
        verbose=False
    )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        js_code=_JS,
        delay_before_return_html=3.0,
        page_timeout=60_000,
        verbose=False,
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)

    if not result.success:
        raise RuntimeError(f"Failed to load page: {result.error_message}")

    if not (m := INJECTED_RE.search(result.html or "")):  # holy walrus operator 
        raise RuntimeError("Injected data not found in html")

    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse injected json: {exc}") from exc
    if data.get("price") is None:
        raise RuntimeError("No price found in json-ld")

    scan = data.get("mainText", "")[:SCAN_WINDOW]
    em = EST_VALUE_RE.search(scan)
    is_on_sale = bool(em or PERCENT_OFF_RE.search(scan))
    current_price = _parse_price(data["price"])
    regular_price = _parse_price(em.group(1)) if (is_on_sale and em) else current_price

    return {
        "product_name":  data.get("name"),
        "is_in_stock":   (data.get("availability") in IN_STOCK_URIS)
                         and not NOT_IN_STOCK_RE.search(scan),
        "is_on_sale":    is_on_sale,
        "regular_price": regular_price,
        "sale_price":    current_price,
    }


def main():
    # enforce utf-8 encoding
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    url = sys.argv[1] if len(sys.argv) > 1 else URL
    print(f"Scraping: {url}")
    print("-" * 60)

    try:
        p = asyncio.run(scrape(url))
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    regular, sale = p["regular_price"], p["sale_price"]
    print(f"Product Name : {p['product_name']}")
    print(f"In Stock : {p['is_in_stock']}")
    print(f"On Sale : {p['is_on_sale']}")
    print(f"Regular Price: {f'${regular:.2f}' if regular is not None else 'N/A'}")
    print(f"Sale Price : {f'${sale:.2f}' if sale is not None else 'N/A'}")


if __name__ == "__main__":
    main()
