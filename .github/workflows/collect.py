# Winrate collector v0.1
# Pulls GETS RSS feeds, always stores the raw XML, then best-effort parses
# new items into per-feed CSVs. Raw storage means a parse failure never
# loses data: it can be reprocessed later in Cowork.

import csv
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEEDS = {
    "gets_all": "https://www.gets.govt.nz/ExternalRSSFeed.htm",
    "gets_moe_school_infra": "https://www.gets.govt.nz/ExternalRSSFeed.htm?clientOrganisationID=72231",
}

HEADERS = {"User-Agent": "WinrateCollector/0.1 (small research collector; two requests per day)"}
STAMP = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


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
    for name, url in FEEDS.items():
        try:
            raw = fetch(url)
            raw_dir = f"data/raw/{name}"
            os.makedirs(raw_dir, exist_ok=True)
            with open(f"{raw_dir}/{STAMP}.xml", "wb") as f:
                f.write(raw)
            try:
                count = append_new(name, parse_items(raw))
                print(f"{name}: {count} new items")
            except Exception as e:
                print(f"{name}: raw saved, parse failed: {e}")
        except Exception as e:
            print(f"{name}: fetch failed: {e}")


if __name__ == "__main__":
    main()
