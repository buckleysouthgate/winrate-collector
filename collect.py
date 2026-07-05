# Winrate collector v0.2
# Pulls candidate GETS feeds, logs exactly what each one returns, stores the raw
# bytes, and best-effort parses items to CSV. Designed to NEVER fail the job:
# collection problems are logged, not raised, so the run stays green and the log
# stays useful for diagnosis.

import csv
import os
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = {
    "vendorpanel_au_all": "https://www.vendorpanel.com.au/PublicTendersRssV2.aspx?mode=all",
    "vendorpanel_nz_all": "https://www.vendorpanel.nz/PublicTendersRssV2.aspx?mode=all",
}


HEADERS = {"User-Agent": "Mozilla/5.0 (WinrateCollector/0.2; low-volume research)"}
STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.headers.get("Content-Type", ""), resp.read()


def parse_items(raw_bytes):
    items = []
    root = ET.fromstring(raw_bytes)
    for item in root.iter("item"):
        def text(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""
        items.append({
            "guid": text("guid") or text("link"),
            "title": text("title"),
            "link": text("link"),
            "pub_date": text("pubDate"),
            "description": text("description")[:1000],
        })
    return items


def append_new(feed_name, items):
    path = f"data/{feed_name}.csv"
    os.makedirs("data", exist_ok=True)
    seen = set()
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            seen = {row["guid"] for row in csv.DictReader(f)}
    new_rows = [i for i in items if i["guid"] and i["guid"] not in seen]
    if not new_rows:
        return 0
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["first_seen", "guid", "title", "link", "pub_date", "description"]
        )
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow({"first_seen": STAMP, **row})
    return len(new_rows)


def main():
    os.makedirs("data/raw", exist_ok=True)
    for name, url in FEEDS.items():
        print(f"--- {name}: {url}")
        try:
            status, ctype, raw = fetch(url)
        except urllib.error.HTTPError as e:
            print(f"  HTTP error {e.code}: feed URL is probably wrong or blocked.")
            continue
        except Exception as e:
            print(f"  fetch failed: {e!r}")
            continue

        print(f"  status={status} content-type={ctype} bytes={len(raw)}")
        raw_dir = f"data/raw/{name}"
        os.makedirs(raw_dir, exist_ok=True)
        with open(f"{raw_dir}/{STAMP}.bin", "wb") as f:
            f.write(raw)

        head = raw[:500]
        if b"<rss" not in head and b"<?xml" not in head and b"<feed" not in head:
            preview = raw[:200].decode("utf-8", "replace").replace("\n", " ")
            print(f"  NOT XML. First 200 chars: {preview}")
            print("  GETS likely does not serve RSS here; collector needs an HTML-scrape approach.")
            continue

        try:
            count = append_new(name, parse_items(raw))
            print(f"  parsed OK, {count} new items")
        except Exception as e:
            print(f"  raw saved, parse failed: {e!r}")


if __name__ == "__main__":
    main()
    sys.exit(0)
