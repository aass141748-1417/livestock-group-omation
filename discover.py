import csv
from pathlib import Path
from urllib.parse import quote_plus

import feedparser


FILE = Path("leads.csv")

FIELDS = [
    "name",
    "phone",
    "interest",
    "category",
    "deal_type",
    "city",
    "source",
    "consent",
    "status",
]

SEARCHES = [
    ("مواشي المدينة المنورة", "مواشي عامة"),
    ("بيع أغنام المدينة المنورة", "غنم"),
    ("شراء أغنام المدينة المنورة", "غنم"),
    ("بيع إبل المدينة المنورة", "إبل"),
    ("شراء إبل المدينة المنورة", "إبل"),
    ("مواشي للبيع المدينة المنورة", "مواشي عامة"),
    ("مواشي شراء المدينة المنورة", "مواشي عامة"),
]


def classify_deal(text):
    text = text.lower()

    if "بيع" in text and "شراء" in text:
        return "بيع وشراء"
    if "بيع" in text or "للبيع" in text:
        return "بيع"
    if "شراء" in text or "مطلوب" in text:
        return "شراء"

    return "عام"


def create_database():
    if not FILE.exists():
        with FILE.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def get_existing_sources():
    sources = set()

    if FILE.exists():
        with FILE.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row.get("source"):
                    sources.add(row["source"])

    return sources


def search_public_results():
    create_database()
    existing_sources = get_existing_sources()
    added = 0

    with FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)

        for query, category in SEARCHES:

            url = (
                "https://news.google.com/rss/search?q="
                + quote_plus(query)
                + "&hl=ar&gl=SA&ceid=SA:ar"
            )

            feed = feedparser.parse(url)

            for entry in feed.entries:
                source = entry.get("link", "").strip()
                title = entry.get("title", "").strip()

                if not source or source in existing_sources:
                    continue

                deal_type = classify_deal(query + " " + title)

                writer.writerow({
                    "name": "",
                    "phone": "",
                    "interest": query,
                    "category": category,
                    "deal_type": deal_type,
                    "city": "المدينة المنورة",
                    "source": source,
                    "consent": "no",
                    "status": "discovered",
                })

                existing_sources.add(source)
                added += 1

    print(f"تم اكتشاف وتصنيف {added} نتيجة جديدة.")


if __name__ == "__main__":
    search_public_results()
